# from expenses.repository import ExpenseRepository


# class ExpenseService:

#     @staticmethod
#     def get_all_expenses():
#         return ExpenseRepository.get_all()

#     @staticmethod
#     def get_expense_by_id(expense_id):
#         return ExpenseRepository.get_by_id(expense_id)

#     @staticmethod
#     def create_expense(data):
#         # Basic validation
#         if not data["title"]:
#             raise ValueError("Expense title is required")

#         if not data["amount"]:
#             raise ValueError("Expense amount is required")

#         ExpenseRepository.create(data)

#     @staticmethod
#     def delete_expense(expense_id):
#         ExpenseRepository.delete(expense_id)
