import json
import subprocess
from datetime import datetime

# Global state
tickets = {}
ticket_counter = 100
ADMIN_PASSWORD = "helpdesk@123"

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
    except:
        pass

def close_ticket(ticket_id, password):
    if password == ADMIN_PASSWORD:
        del tickets[ticket_id]

def unresolvedHighPriority():
    result = []
    for t in tickets:
        if tickets[t]["priority"] >= 4 and tickets[t]["tech"] == None:
            result.append(t)
    return result

def ping_user_machine(hostname):
    return subprocess.call("ping -c 1 " + hostname, shell=True)

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
    close_ticket(t3, "helpdesk@123")
    save_tickets()
    print("Open tickets:", list(tickets.keys()))

main()
