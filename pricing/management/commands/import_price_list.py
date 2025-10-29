import csv
import os
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pricing.models import TestCategory, TestSubCategory, TestItem


class Command(BaseCommand):
    help = 'Import master price list from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file containing the master price list'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before importing',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing',
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        clear_existing = options['clear']
        dry_run = options['dry_run']

        # Check if file exists
        if not os.path.exists(csv_file_path):
            raise CommandError(f'CSV file does not exist: {csv_file_path}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No data will be imported')
            )

        # Clear existing data if requested
        if clear_existing and not dry_run:
            self.stdout.write('Clearing existing pricing data...')
            TestItem.objects.all().delete()
            TestSubCategory.objects.all().delete()
            TestCategory.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('Existing data cleared')
            )

        # Import data
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.import_data(reader, dry_run)
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')

    def import_data(self, reader, dry_run=False):
        """Import data from CSV reader"""
        categories_created = 0
        subcategories_created = 0
        test_items_created = 0
        errors = []

        with transaction.atomic():
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header
                try:
                    # Process category
                    category_code = row['category_code'].strip()
                    category_name = row['category_name'].strip()
                    
                    if not dry_run:
                        category, cat_created = TestCategory.objects.get_or_create(
                            code=category_code,
                            defaults={'name': category_name}
                        )
                        if cat_created:
                            categories_created += 1
                    else:
                        category = None
                        cat_created = True  # Assume new for dry run
                        if cat_created:
                            categories_created += 1

                    # Process subcategory
                    subcategory_name = row['sub_category'].strip()
                    
                    if not dry_run:
                        subcategory, subcat_created = TestSubCategory.objects.get_or_create(
                            category=category,
                            name=subcategory_name,
                            defaults={'description': f'Subcategory for {category_name}'}
                        )
                        if subcat_created:
                            subcategories_created += 1
                    else:
                        subcategory = None
                        subcat_created = True  # Assume new for dry run
                        if subcat_created:
                            subcategories_created += 1

                    # Process test item
                    system_code = row['system_code'].strip()
                    display_code = row['display_code'].strip()
                    test_name = row['test_name'].strip()
                    method_standard = row['method_standard'].strip()
                    unit = row['unit'].strip()
                    currency = row['currency'].strip()
                    price = Decimal(row['price'].strip())
                    tat_days = int(row['tat_days'].strip())
                    sample_type = row['sample_type'].strip()
                    is_active = row['is_active'].strip().lower() == 'true'
                    notes = row['notes'].strip() if row['notes'] else None

                    if not dry_run:
                        test_item, item_created = TestItem.objects.get_or_create(
                            system_code=system_code,
                            defaults={
                                'display_code': display_code,
                                'category': category,
                                'subcategory': subcategory,
                                'test_name': test_name,
                                'method_standard': method_standard,
                                'unit': unit,
                                'currency': currency,
                                'price': price,
                                'tat_days': tat_days,
                                'sample_type': sample_type,
                                'is_active': is_active,
                                'notes': notes,
                            }
                        )
                        if item_created:
                            test_items_created += 1
                    else:
                        item_created = True  # Assume new for dry run
                        if item_created:
                            test_items_created += 1

                except Exception as e:
                    error_msg = f'Row {row_num}: {str(e)}'
                    errors.append(error_msg)
                    self.stdout.write(
                        self.style.ERROR(error_msg)
                    )

        # Report results
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN COMPLETE - Would create:\n'
                    f'  Categories: {categories_created}\n'
                    f'  Subcategories: {subcategories_created}\n'
                    f'  Test Items: {test_items_created}\n'
                    f'  Errors: {len(errors)}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Import completed successfully!\n'
                    f'  Categories created: {categories_created}\n'
                    f'  Subcategories created: {subcategories_created}\n'
                    f'  Test Items created: {test_items_created}\n'
                    f'  Errors: {len(errors)}'
                )
            )

        if errors:
            self.stdout.write(
                self.style.WARNING(f'\nErrors encountered:\n' + '\n'.join(errors))
            )
