class User:
    def __init__(
        self,
        id,
        email,
        password_hash,
        full_name,
        is_active,
        must_change_password=False
    ):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.is_active = is_active
        self.must_change_password = must_change_password
