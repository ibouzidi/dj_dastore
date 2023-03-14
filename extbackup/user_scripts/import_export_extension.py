import csv
from django.apps import apps
from io import StringIO
from extbackup.models import SupportedExtension


def export_supported_extensions_to_csv():
    # Get the SupportedExtension model
    model = apps.get_model('extbackup', 'SupportedExtension')

    # Get all instances of the model
    all_extensions = SupportedExtension.objects.all()

    # Create a StringIO object to hold the CSV data
    csv_data = StringIO()

    # Create a CSV writer and write the header row
    writer = csv.writer(csv_data)
    writer.writerow(['extension'])

    # Write each instance to the CSV file
    for i in all_extensions:
        writer.writerow([i.extension])

    # Save the CSV file
    with open('supported_extensions.csv', 'w') as csv_file:
        csv_file.write(csv_data.getvalue())


# def import_supported_extensions_from_csv():
#     # Read CSV data
#     with open('supported_extensions.csv', 'r') as csv_file:
#         csv_reader = csv.reader(csv_file)
#         next(csv_reader)  # Skip header row
#         for row in csv_reader:
#             _, created = SupportedExtension.objects.get_or_create(extension=row[0])
#
#     # Reset database sequence numbers
#     call_command('sqlsequencereset', 'extbackup')