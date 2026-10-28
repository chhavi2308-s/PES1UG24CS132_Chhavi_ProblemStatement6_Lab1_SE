import hmac
import json
import os
import re
import shutil
import subprocess  # nosec B404 - only used to run ping, never through a shell
from datetime import datetime

# Global state
tickets = {}
ticket_counter = 100

# Hostnames: letters, digits, dots and hyphens; must start/end alphanumeric
# (this also stops a hostname from being parsed as a ping option like "-f").
HOSTNAME_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?")

def raise_ticket(user, issue_type, urgency="3", audit_trail=[]):
    global ticket_counter
    ticket_counter += 1
    tickets[ticket_counter] = {"user": user, "issue": issue_type, "priority": int(urgency), "tech": None, "notes": []}
    audit_trail.append("%s raised #%d at %s" % (user, ticket_counter, datetime.now()))
    return ticket_counter

def assign_ticket(ticket_id, technician):
    tickets[ticket_id]["tech"] = technician

def add_note(ticket_id, note):
    try:
        tickets[ticket_id]["notes"].append(note)
    except KeyError:
        return False
    return True

def close_ticket(ticket_id, password):
    # The admin password comes from the environment, never from source code.
    admin_password = os.environ.get("HELPDESK_ADMIN_PASSWORD", "")
    if not admin_password:
        return False
    if not hmac.compare_digest(password.encode("utf-8"), admin_password.encode("utf-8")):
        return False
    return tickets.pop(ticket_id, None) is not None

def unresolvedHighPriority():
    result = []
    for t in tickets:
        if tickets[t]["priority"] >= 4 and tickets[t]["tech"] == None:
            result.append(t)
    return result

def ping_user_machine(hostname):
    if not HOSTNAME_PATTERN.fullmatch(hostname):
        raise ValueError("Invalid hostname: %r" % hostname)
    ping_path = shutil.which("ping")
    if ping_path is None:
        raise FileNotFoundError("ping executable not found")
    # Argument list + no shell: the hostname can never be run as a command.
    return subprocess.call([ping_path, "-c", "1", hostname])  # nosec B603

def save_tickets(file="tickets.json"):
    f = open(file, "w")
    f.write(json.dumps(tickets))
    f.close()

def main():
    t1 = raise_ticket("anil", "printer", "5")
    t2 = raise_ticket("meera", "wifi", "4")
    t3 = raise_ticket("joe", "vpn", "-7")
    assign_ticket(t1, "Tech-Kiran")
    add_note(999, "Called user")
    print("Unassigned high priority:", unresolvedHighPriority())
    level = input("Urgency for a new laptop ticket (1-5, Enter for 3): ") or "3"
    raise_ticket("sana", "laptop", level)
    close_ticket(t3, os.environ.get("HELPDESK_ADMIN_PASSWORD", ""))
    save_tickets()
    print("Open tickets:", list(tickets.keys()))

main()
