from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Group, GroupMember, Expense, ExpensePayment, ExpenseSplit

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class GroupSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'created_by', 'created_at']

class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = GroupMember
        fields = ['id', 'group', 'user', 'user_id']

class ExpensePaymentSerializer(serializers.ModelSerializer):
    payer_username = serializers.CharField(source='payer.username', read_only=True)
    
    class Meta:
        model = ExpensePayment
        fields = ['id', 'payer', 'payer_username', 'amount']

class ExpenseSplitSerializer(serializers.ModelSerializer):
    member_username = serializers.CharField(source='member.username', read_only=True)
    
    class Meta:
        model = ExpenseSplit
        fields = ['id', 'member', 'member_username', 'share']

class ExpenseSerializer(serializers.ModelSerializer):
    payments = ExpensePaymentSerializer(many=True, read_only=True)
    splits = ExpenseSplitSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = Expense
        fields = ['id', 'group', 'description', 'date', 'created_at', 'payments', 'splits', 'total_amount']
        read_only_fields = ['group']
    
    def get_total_amount(self, obj):
        # Total amount is the sum of all splits (what needs to be divided)
        return sum(split.share for split in obj.splits.all())
