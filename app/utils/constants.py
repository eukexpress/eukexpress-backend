# Status and intervention constants

SHIPMENT_STATUSES = {
    'BOOKED': 'Booked',
    'COLLECTED': 'Collected',
    'WAREHOUSE_PROCESSING': 'Warehouse Processing',
    'TERMINAL_ARRIVAL': 'Terminal Arrival',
    'EN_ROUTE': 'En Route',
    'CUSTOMS_BOND': 'Customs Bond',
    'CUSTOMS_CLEARED': 'Customs Cleared',
    'SECURITY_HOLD': 'Security Hold',
    'SECURITY_CLEARED': 'Security Cleared',
    'DAMAGE_REPORTED': 'Damage Reported',
    'DAMAGE_RESOLVED': 'Damage Resolved',
    'RETURN_TO_SENDER': 'Return to Sender',
    'TRANSIT_EXCEPTION': 'Transit Exception',
    'DESTINATION_HUB': 'Destination Hub',
    'WITH_COURIER': 'With Courier',
    'DELIVERED': 'Delivered'
}

STATUS_COLORS = {
    'BOOKED': 'blue',
    'COLLECTED': 'blue',
    'WAREHOUSE_PROCESSING': 'blue',
    'TERMINAL_ARRIVAL': 'blue',
    'EN_ROUTE': 'green',
    'CUSTOMS_BOND': 'red',
    'CUSTOMS_CLEARED': 'green',
    'SECURITY_HOLD': 'orange',
    'SECURITY_CLEARED': 'green',
    'DAMAGE_REPORTED': 'red',
    'DAMAGE_RESOLVED': 'green',
    'RETURN_TO_SENDER': 'orange',
    'TRANSIT_EXCEPTION': 'orange',
    'DESTINATION_HUB': 'blue',
    'WITH_COURIER': 'blue',
    'DELIVERED': 'green'
}

INTERVENTION_TYPES = ['customs', 'security', 'damage', 'return', 'delay']