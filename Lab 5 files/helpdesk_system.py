"""IT helpdesk ticket allocator.

Raises tickets with an urgency level, assigns technicians, records notes,
lists unassigned high-priority tickets and saves everything to a JSON file.

The admin password needed to close tickets is read from the
HELPDESK_ADMIN_PASSWORD environment variable and is never stored in code.
"""
import hmac
import itertools
import json
import os
import re
import shutil
import subprocess  # nosec B404 - only used to run ping, never through a shell
from datetime import datetime

MIN_URGENCY = 1
MAX_URGENCY = 5
HIGH_PRIORITY = 4
DEFAULT_URGENCY = "3"

# Hostnames: letters, digits, dots and hyphens; must start/end alphanumeric
# (this also stops a hostname from being parsed as a ping option like "-f").
HOSTNAME_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?")

# Global state
tickets = {}
audit_log = []
_ticket_ids = itertools.count(101)

def parse_urgency(value):
    """Convert user input to an int between MIN_URGENCY and MAX_URGENCY.

    Raises ValueError if the value is not a whole number in that range.
    """
    try:
        urgency = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Urgency must be a whole number, got {value!r}") from None
    if not MIN_URGENCY <= urgency <= MAX_URGENCY:
        raise ValueError(f"Urgency must be {MIN_URGENCY}-{MAX_URGENCY}, got {urgency}")
    return urgency

def raise_ticket(user, issue_type, urgency=DEFAULT_URGENCY, audit_trail=None):
    """Create a ticket and return its id.

    Raises ValueError (before any ticket is created) if urgency is invalid.
    If no audit_trail list is given, the module-level audit_log is used.
    """
    priority = parse_urgency(urgency)
    if audit_trail is None:
        audit_trail = audit_log
    ticket_id = next(_ticket_ids)
    tickets[ticket_id] = {"user": user, "issue": issue_type, "priority": priority, "tech": None, "notes": []}
    audit_trail.append(f"{user} raised #{ticket_id} at {datetime.now()}")
    return ticket_id

def assign_ticket(ticket_id, technician):
    """Assign a technician to a ticket. Return False if the ticket is unknown."""
    if ticket_id not in tickets:
        return False
    tickets[ticket_id]["tech"] = technician
    return True

def add_note(ticket_id, note):
    """Append a note to a ticket. Return False if the ticket is unknown."""
    try:
        tickets[ticket_id]["notes"].append(note)
    except KeyError:
        return False
    return True

def close_ticket(ticket_id, password):
    """Close (delete) a ticket if the admin password is correct.

    Return True only if a ticket was actually closed.
    """
    admin_password = os.environ.get("HELPDESK_ADMIN_PASSWORD", "")
    if not admin_password:
        return False
    if not hmac.compare_digest(password.encode("utf-8"), admin_password.encode("utf-8")):
        return False
    return tickets.pop(ticket_id, None) is not None

def unresolved_high_priority():
    """Return ids of high-priority tickets that have no technician yet."""
    return [
        ticket_id
        for ticket_id, ticket in tickets.items()
        if ticket["priority"] >= HIGH_PRIORITY and ticket["tech"] is None
    ]

def ping_user_machine(hostname):
    """Ping a host once and return ping's exit code (0 means reachable)."""
    if not HOSTNAME_PATTERN.fullmatch(hostname):
        raise ValueError(f"Invalid hostname: {hostname!r}")
    ping_path = shutil.which("ping")
    if ping_path is None:
        raise FileNotFoundError("ping executable not found")
    # Argument list + no shell: the hostname can never be run as a command.
    return subprocess.call([ping_path, "-c", "1", hostname])  # nosec B603

def save_tickets(filename="tickets.json"):
    """Write all tickets to a JSON file."""
    with open(filename, "w", encoding="utf-8") as handle:
        json.dump(tickets, handle)

def main():
    """Run the demo scenario."""
    t1 = raise_ticket("anil", "printer", "5")
    t2 = raise_ticket("meera", "wifi", "4")
    try:
        raise_ticket("joe", "vpn", "-7")
    except ValueError as error:
        print("Ticket rejected:", error)
    assign_ticket(t1, "Tech-Kiran")
    if not add_note(999, "Called user"):
        print("Note not added: ticket #999 does not exist")
    print("Unassigned high priority:", unresolved_high_priority())
    level = input("Urgency for a new laptop ticket (1-5, Enter for 3): ") or DEFAULT_URGENCY
    try:
        raise_ticket("sana", "laptop", level)
    except ValueError as error:
        print("Ticket rejected:", error)
    if close_ticket(t2, os.environ.get("HELPDESK_ADMIN_PASSWORD", "")):
        print(f"Closed ticket #{t2}")
    else:
        print(f"Ticket #{t2} not closed (admin password missing or wrong)")
    save_tickets()
    print("Open tickets:", list(tickets))

if __name__ == "__main__":
    main()
