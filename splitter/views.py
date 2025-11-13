from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Group, GroupMember, Expense, ExpensePayment, ExpenseSplit
from .serializers import GroupSerializer, GroupMemberSerializer, ExpenseSerializer
from decimal import Decimal
import json

User = get_user_model()

@csrf_exempt
@api_view(['POST'])
def create_user(request):
    data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password', 'password123')

    if not username:
        return Response({'error': 'username is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=username)
        created = False
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            email=email or f'{username}@example.com',
            password=password
        )
        created = True

    return Response({'id': user.id, 'username': user.username, 'email': user.email})

class GroupListCreate(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def perform_create(self, serializer):
        # If created_by is not provided, create a default user or use the first user
        created_by = serializer.validated_data.get('created_by')
        if not created_by:
            # Try to get or create a default user
            default_user, _ = User.objects.get_or_create(
                username='default_user',
                defaults={'email': 'default@example.com'}
            )
            group = serializer.save(created_by=default_user)
            # Add creator as member
            GroupMember.objects.get_or_create(group=group, user=default_user)
        else:
            group = serializer.save()
            # Add creator as member
            GroupMember.objects.get_or_create(group=group, user=created_by)

class AddMemberView(generics.GenericAPIView):
    serializer_class = GroupMemberSerializer

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, group_id):
        print(f"AddMemberView called with group_id={group_id}")
        print(f"Request data: {request.data}")
        
        group = get_object_or_404(Group, pk=group_id)
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, pk=user_id)
        gm, created = GroupMember.objects.get_or_create(group=group, user=user)
        return Response({'id': gm.id, 'created': created}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ExpenseListCreate(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        return Expense.objects.filter(group_id=group_id)

    def perform_create(self, serializer):
        group_id = self.kwargs['group_id']
        group = get_object_or_404(Group, pk=group_id)

        # Handle multiple payments
        payments_data = self.request.data.get('payments', [])
        if payments_data:
            for payment_data in payments_data:
                payer_id = payment_data.get('payer')
                amount = Decimal(payment_data.get('amount'))

                if not payer_id:
                    raise serializers.ValidationError({'payments': 'Payer ID is required for each payment'})
                if not amount:
                    raise serializers.ValidationError({'payments': 'Amount is required for each payment'})

                if not GroupMember.objects.filter(group=group, user_id=payer_id).exists():
                    raise serializers.ValidationError(
                        {'payer': f'Payer with ID {payer_id} must be a member of the group'}
                    )

        # Handle splits
        splits_data = self.request.data.get('splits', [])
        if splits_data:
            for split_data in splits_data:
                member_id = split_data.get('member')
                share = split_data.get('share')

                if not member_id:
                    raise serializers.ValidationError({'splits': 'Member ID is required for each split'})
                if share is None or share == '':
                    raise serializers.ValidationError({'splits': 'Share is required for each split'})

                if not GroupMember.objects.filter(group=group, user_id=member_id).exists():
                    raise serializers.ValidationError(
                        {'member': f'Member with ID {member_id} must be a member of the group'}
                    )

        expense = serializer.save(group=group)

        # Create Payment objects
        for payment_data in payments_data:
            payer_id = payment_data.get('payer')
            amount = Decimal(payment_data.get('amount'))
            ExpensePayment.objects.create(expense=expense, payer_id=payer_id, amount=amount)

        # Create Split objects
        for split_data in splits_data:
            member_id = split_data.get('member')
            share = Decimal(split_data.get('share'))
            ExpenseSplit.objects.create(expense=expense, member_id=member_id, share=share)


@csrf_exempt
@api_view(['GET'])
def get_group_members(request, group_id):
    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        return Response({'error': 'Group not found'}, status=404)

    members = GroupMember.objects.filter(group=group).select_related('user')
    return Response([{
        'id': m.user.id,
        'username': m.user.username,
        'email': m.user.email
    } for m in members])

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.http import HttpResponse
from io import BytesIO

@csrf_exempt
@api_view(['GET'])
def download_report_pdf(request, group_id):
    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        return HttpResponse('Group not found', status=404)

    members_qs = GroupMember.objects.filter(group=group).select_related('user')
    members = list(members_qs)

    if not members:
        return HttpResponse('No members in this group', status=400)

    member_ids = [m.user.id for m in members]
    expenses = Expense.objects.filter(group=group).prefetch_related('payments', 'splits')

    paid_by = {}
    owes = {}
    for m in members:
        paid_by[m.user.id] = Decimal('0.00')
        owes[m.user.id] = Decimal('0.00')

    # Calculate what each person paid
    for exp in expenses:
        for payment in exp.payments.all():
            paid_by[payment.payer.id] += payment.amount

    # Calculate what each person owes
    for exp in expenses:
        for split in exp.splits.all():
            owes[split.member.id] += split.share

    # Calculate net balance
    net_balance = {}
    for m in members:
        net = paid_by[m.user.id] - owes[m.user.id]
        net_balance[m.user.id] = net

    creditors = []
    debtors = []
    for uid, net in net_balance.items():
        if net > Decimal('0.01'):
            creditors.append({'user_id': uid, 'amount': net})
        elif net < Decimal('-0.01'):
            debtors.append({'user_id': uid, 'amount': -net})

    creditors.sort(key=lambda x: x['amount'], reverse=True)
    debtors.sort(key=lambda x: x['amount'], reverse=True)

    settlements = []
    i, j = 0, 0
    while i < len(creditors) and j < len(debtors):
        cred = creditors[i]
        debt = debtors[j]
        settle_amount = min(cred['amount'], debt['amount'])

        settlements.append({
            'from_user': debt['user_id'],
            'to_user': cred['user_id'],
            'amount': float(settle_amount)
        })

        cred['amount'] -= settle_amount
        debt['amount'] -= settle_amount

        if cred['amount'] < Decimal('0.01'):
            i += 1
        if debt['amount'] < Decimal('0.01'):
            j += 1

    user_id_to_name = {}
    for m in members:
        user_id_to_name[m.user.id] = m.user.username

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=20
    )

    # Title
    title = Paragraph(f"Settlement Report: {group.name}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))

    # Member Balances Section
    balances_heading = Paragraph("Member Balances", heading_style)
    elements.append(balances_heading)

    balance_data = [['Member', 'Balance']]
    for m in members:
        balance = float(net_balance[m.user.id])
        balance_str = f"${balance:+.2f}" if balance != 0 else "$0.00"
        balance_data.append([m.user.username, balance_str])

    balance_table = Table(balance_data, colWidths=[3*inch, 2*inch])
    balance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
    ]))
    elements.append(balance_table)
    elements.append(Spacer(1, 0.4*inch))

    # Settlements Section
    settlements_heading = Paragraph("Settlements Needed", heading_style)
    elements.append(settlements_heading)

    if settlements:
        settlement_data = [['From', 'To', 'Amount']]
        for s in settlements:
            from_user = user_id_to_name.get(s['from_user'], 'Unknown')
            to_user = user_id_to_name.get(s['to_user'], 'Unknown')
            settlement_data.append([from_user, to_user, f"${s['amount']:.2f}"])

        settlement_table = Table(settlement_data, colWidths=[2*inch, 2*inch, 1.5*inch])
        settlement_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        elements.append(settlement_table)
    else:
        all_settled = Paragraph("All settled up! 🎉", styles['Normal'])
        elements.append(all_settled)

    elements.append(Spacer(1, 0.4*inch))

    # Expense History Section
    expense_history_heading = Paragraph("Expense History", heading_style)
    elements.append(expense_history_heading)

    if expenses:
        expense_data = [['Description', 'Total', 'Paid By', 'Split Among']]
        for exp in expenses:
            # Calculate total expense from splits
            total_exp = sum(split.share for split in exp.splits.all())
            
            # Get payers info
            payers_info = []
            for payment in exp.payments.all():
                payer_name = user_id_to_name.get(payment.payer.id, 'Unknown')
                payers_info.append(f"{payer_name} (${payment.amount:.2f})")
            payers_str = ', '.join(payers_info) if payers_info else 'N/A'
            
            # Get split members info
            split_members = []
            for split in exp.splits.all():
                member_name = user_id_to_name.get(split.member.id, 'Unknown')
                split_members.append(f"{member_name} (${split.share:.2f})")
            splits_str = ', '.join(split_members) if split_members else 'N/A'
            
            expense_data.append([
                exp.description or 'No description',
                f"${total_exp:.2f}",
                payers_str,
                splits_str
            ])

        expense_table = Table(expense_data, colWidths=[1.8*inch, 0.8*inch, 1.8*inch, 1.8*inch])
        expense_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elements.append(expense_table)
    else:
        no_expenses = Paragraph("No expenses recorded yet.", styles['Normal'])
        elements.append(no_expenses)

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="settlement_report_{group.name}.pdf"'
    return response

@csrf_exempt
@api_view(['GET'])
def group_report(request, group_id):
    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        return Response({'error': 'Group not found'}, status=404)

    members_qs = GroupMember.objects.filter(group=group).select_related('user')
    members = list(members_qs)
    if not members:
        return Response({
            'group': group.name,
            'members': [],
            'balances': {},
            'settlements': []
        })

    member_ids = [m.user.id for m in members]
    expenses = Expense.objects.filter(group=group).prefetch_related('payments', 'splits')

    paid_by = {}
    owes = {}
    for m in members:
        paid_by[m.user.id] = Decimal('0.00')
        owes[m.user.id] = Decimal('0.00')

    # Calculate what each person paid
    for exp in expenses:
        for payment in exp.payments.all():
            paid_by[payment.payer.id] += payment.amount

    # Calculate what each person owes
    for exp in expenses:
        for split in exp.splits.all():
            owes[split.member.id] += split.share

    # Calculate net balance
    net_balance = {}
    for m in members:
        net = paid_by[m.user.id] - owes[m.user.id]
        net_balance[m.user.id] = net

    creditors = []
    debtors = []
    for uid, net in net_balance.items():
        if net > Decimal('0.01'):
            creditors.append({'user_id': uid, 'amount': net})
        elif net < Decimal('-0.01'):
            debtors.append({'user_id': uid, 'amount': -net})

    creditors.sort(key=lambda x: x['amount'], reverse=True)
    debtors.sort(key=lambda x: x['amount'], reverse=True)

    settlements = []
    i, j = 0, 0
    while i < len(creditors) and j < len(debtors):
        cred = creditors[i]
        debt = debtors[j]
        settle_amount = min(cred['amount'], debt['amount'])

        settlements.append({
            'from_user': debt['user_id'],
            'to_user': cred['user_id'],
            'amount': float(settle_amount)
        })

        cred['amount'] -= settle_amount
        debt['amount'] -= settle_amount

        if cred['amount'] < Decimal('0.01'):
            i += 1
        if debt['amount'] < Decimal('0.01'):
            j += 1

    balances_display = {}
    members_info = []
    for m in members:
        balances_display[m.user.username] = float(net_balance[m.user.id])
        members_info.append({
            'id': m.user.id,
            'username': m.user.username,
            'balance': float(net_balance[m.user.id])
        })

    return Response({
        'group': group.name,
        'members': members_info,
        'balances': balances_display,
        'settlements': settlements
    })