"""
Specify which dates and users to update
"""

from modules.update_handler import manualschedule

if __name__ == '__main__':
    N = 3  # patient participated for N days
    M = 4  # study began M days ago (from when you run this script)
    user_id = ""

    for i in range(N):
        days = M-i
        manualschedule(days, user_id)
