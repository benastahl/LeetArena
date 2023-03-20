from datetime import datetime


class User:
    def __init__(self, entry_id, email, username, hashed_password, auth_token, creation_date, admin):
        self.entry_id = entry_id

        self.email = email
        self.username = username
        self.hashed_password = hashed_password
        self.auth_token = auth_token
        self.creation_date = datetime.fromtimestamp(creation_date)

        # Special Roles
        self.admin = bool(admin)


# Experimental
class Statistics:
    def __init__(self,
                 current_user_count,
                 all_time_user_count,
                 staff_count,

                 deliveries_scheduled,
                 deliveries_successful,
                 availabilities_scheduled,

                 gross_fees_income,
                 gross_spent_by_users,

                 ):
        # Users
        self.current_user_count = current_user_count
        self.all_time_user_count = all_time_user_count
        self.staff_count = staff_count

        # Deliveries
        self.deliveries_scheduled_count = deliveries_scheduled
        self.deliveries_successful_count = deliveries_successful
        self.availabilities_scheduled_count = availabilities_scheduled

        # Finances
        self.gross_fees_income = gross_fees_income
        self.gross_spent_by_users = gross_spent_by_users




