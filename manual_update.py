"""
Specify which dates and users to update
"""

from datetime import date, datetime
from modules.update_handler import manualschedule

def run(user_id, start_date, end_date):
    # create date object from string
    _start_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
    _end_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

    # invalid dates entered
    if (_start_obj > _end_obj) or (_start_obj > date.today()):
        print("Please check start and end dates.")
    else:
        _N = (_end_obj - _start_obj).days
        _M = (date.today() - _start_obj).days
        for i in range(_N):
            days = _M - i
            manualschedule(days, user_id)

if __name__ == '__main__':
    #  Enter patient data here
    user_id = "BMYN3F"
    study_start_date = "2023-07-28"  # Format dates: '%Y-%m-%d'
    study_end_date = "2023-07-31"
    #
    run(user_id, study_start_date, study_end_date)


