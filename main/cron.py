
from main.models import *
from datetime import *
# import logging

from main.views import notifications 

def delete_leave_notification():                            #cron daily
    try:
        # UserLeaveStatus.objects.filter(rejected = True, to_date = '2022-02-22')
        id_Queryset = UserLeaveStatus.objects.filter(to_date__lte = datetime.today().strftime('%Y-%m-%d')).values_list('id', flat=True)              #check: gets all leaves with to_date today (expired/not expired)
    except:
        print('Log: Error in cron, id retrieval for leave', datetime.now())                                   #log

    try:
        Notification.objects.filter(checked=True, expired=False, taskId__in=id_Queryset).update(expired=True)               #updates only those which are not already expired
    except:
        print('Log: Error in cron, expired updation, for leave notification to_date',datetime.today().strftime('%Y-%m-%d'), 'ON', datetime.now())       #log

    print('Log: Leave Notification Expired to_date',datetime.today().strftime('%Y-%m-%d'), 'on' ,datetime.now())                                        #log

def delete_timetable_notification():                        #cron weekly
    try:
        Notification.objects.filter(checked=True, expired=False, notification_type='TTC').update(expired=True)              #updates only those which are not already expired
    except:
        print('Log: Error in cron, expiry updation for timetable notification ', 'ON', datetime.now())        #log
    
    print('Log: Timetable Notification Expired on' ,datetime.now())                                           #log

def delete_inventory_notification():                        #cron weekly
    try:
        Notification.objects.filter(checked=True, expired=False, notification_type='INVENTORY').update(expired=True)        #updates only those which are not already expired
    except:
        print('Log: Error in cron, expiry updation for inventory notification ', 'ON', datetime.now())        #log
    
    print('Log: Inventory Notification Expired on' ,datetime.now())  

def delete_techResolve_notification():                      #cron weekly
    try:
        Notification.objects.filter(checked=True, expired=False, notification_type='TECH_RESOLVE').update(expired=True)       #updates only those which are not already expired
    except:
        print('Log: Error in cron, expiry updation for tech resolve notification ', 'ON', datetime.now())     #log
    
    print('Log: Tech_Resolve Notification Expired on' ,datetime.now())  
