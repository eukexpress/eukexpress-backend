"""
Services Module
"""
from app.services.email_service import email_service
from app.services.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
    authenticate_admin,
    get_current_user,
    decode_token,
    change_password,
    update_last_login
)
from app.services.shipment_service import (
    create_shipment,
    update_shipment_status,
    get_shipment_by_tracking,
    get_shipments_list,
    get_shipment_filters
)
from app.services.intervention_service import (
    toggle_customs_bond,
    toggle_security_hold,
    report_damage,
    resolve_damage,
    initiate_return,
    cancel_return,
    report_delay,
    resolve_delay
)
from app.services.dashboard_service import get_dashboard_stats
from app.services.keep_alive import keep_alive_service

__all__ = [
    "email_service",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "authenticate_admin",
    "get_current_user",
    "decode_token",
    "change_password",
    "update_last_login",
    "create_shipment",
    "update_shipment_status",
    "get_shipment_by_tracking",
    "get_shipments_list",
    "get_shipment_filters",
    "toggle_customs_bond",
    "toggle_security_hold",
    "report_damage",
    "resolve_damage",
    "initiate_return",
    "cancel_return",
    "report_delay",
    "resolve_delay",
    "get_dashboard_stats",
    "keep_alive_service"
]
