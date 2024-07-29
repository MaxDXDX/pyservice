"""Start python script."""

from calculator import manager

me = manager.get_my_microservice_from_cluster()
print(f'Hello! I am: {me}')

print('Calculating the sum of FIVE and FOUR ...')
result = manager.execute_celery_task(
    f'{manager.app_ref}.sum_two_numbers', (5, 4),)
print(f'5 + 4 = {result} !')
