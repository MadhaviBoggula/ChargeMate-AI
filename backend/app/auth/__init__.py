"""Auth module - owned by Member 1.

Contains: JWT issuance/verification, password hashing, current-user
dependency, role guards, ownership authorization patterns.
Member 4's chat layer consumes ``app.api.deps.current_user`` once landed.
"""
