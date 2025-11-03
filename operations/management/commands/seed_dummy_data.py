"""
Django management command to seed the database with dummy data
Creates 30 Ugandan clients and 40 samples with various tests
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from core.models import User
from operations.models import Client, Sample, SampleTest, SampleStatusHistory
from pricing.models import TestItem


class Command(BaseCommand):
    help = 'Seed the database with 30 Ugandan clients and 40 samples with various tests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing dummy data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing dummy data...'))
            # Clear seeded clients by matching known company names
            seed_companies = [
                'Kampala Construction Ltd', 'Mukono Builders', 'Jinja Engineering Solutions',
                'Entebbe Materials Supply', 'Masaka Civil Works', 'Mbale Infrastructure Group',
                'Gulu Development Corporation', 'Arua Construction Services', 'Lira Building Materials',
                'Mbarara Civil Engineering', 'Fort Portal Projects', 'Tororo Industrial Ltd',
                'Soroti Construction Co', 'Kasese Mining Services', 'Bushenyi Engineering',
                'Iganga Development Agency', 'Kabale Builders Association', 'Hoima Oil & Gas Services',
                'Masindi Civil Contractors', 'Mityana Construction Group', 'Wakiso Developers Ltd',
                'Mukono Real Estate', 'Ntungamo Builders Co', 'Rukungiri Infrastructure',
                'Kanungu Engineering Services', 'Bundibugyo Construction', 'Kamwenge Materials Supply',
                'Kyenjojo Builders', 'Kabarole Projects Ltd', 'Ntoroko Development Co'
            ]
            for company_name in seed_companies:
                Client.objects.filter(name=company_name).delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing dummy data.'))

        # Ugandan company names and locations
        ugandan_companies = [
            ('Kampala Construction Ltd', 'James Mulindwa', 'Plot 45, Industrial Area, Kampala', '+256 700 123456', 'info@kampalaconst.co.ug', '800123456789'),
            ('Mukono Builders', 'Sarah Nakato', 'Main Street, Mukono', '+256 700 234567', 'contact@mukonobuilders.ug', '800234567890'),
            ('Jinja Engineering Solutions', 'Peter Okello', 'Highway Road, Jinja', '+256 700 345678', 'info@jinjaengineering.ug', '800345678901'),
            ('Entebbe Materials Supply', 'Grace Nalubega', 'Airport Road, Entebbe', '+256 700 456789', 'sales@entebbematerials.ug', '800456789012'),
            ('Masaka Civil Works', 'David Ssemwogerere', 'Mbarara Road, Masaka', '+256 700 567890', 'info@masakacivil.ug', '800567890123'),
            ('Mbale Infrastructure Group', 'Mary Nabukeera', 'Main Street, Mbale', '+256 700 678901', 'contact@mbaleinfra.ug', '800678901234'),
            ('Gulu Development Corporation', 'Joseph Ocen', 'Acholi Road, Gulu', '+256 700 789012', 'info@guludev.ug', '800789012345'),
            ('Arua Construction Services', 'Betty Aliro', 'Okapi Road, Arua', '+256 700 890123', 'sales@aruaconst.ug', '800890123456'),
            ('Lira Building Materials', 'Moses Otim', 'Obote Avenue, Lira', '+256 700 901234', 'info@lirabuilding.ug', '800901234567'),
            ('Mbarara Civil Engineering', 'Agnes Tushabe', 'Rwizi Road, Mbarara', '+256 700 012345', 'contact@mbararacivil.ug', '800012345678'),
            ('Fort Portal Projects', 'Charles Mugabe', 'Kabale Road, Fort Portal', '+256 701 123456', 'info@fortportalproj.ug', '801123456789'),
            ('Tororo Industrial Ltd', 'Florence Achieng', 'Busia Road, Tororo', '+256 701 234567', 'sales@tororoind.ug', '801234567890'),
            ('Soroti Construction Co', 'John Opio', 'Main Street, Soroti', '+256 701 345678', 'info@soroticonst.ug', '801345678901'),
            ('Kasese Mining Services', 'Robert Bwambale', 'Kikorongo Road, Kasese', '+256 701 456789', 'contact@kasesemining.ug', '801456789012'),
            ('Bushenyi Engineering', 'Priscilla Nalumansi', 'Mbarara Road, Bushenyi', '+256 701 567890', 'info@bushenyieng.ug', '801567890123'),
            ('Iganga Development Agency', 'Isaac Waiswa', 'Highway Road, Iganga', '+256 701 678901', 'sales@igangadev.ug', '801678901234'),
            ('Kabale Builders Association', 'Rose Tumuhimbise', 'Kisoro Road, Kabale', '+256 701 789012', 'info@kabalebuilders.ug', '801789012345'),
            ('Hoima Oil & Gas Services', 'Michael Byaruhanga', 'Buliisa Road, Hoima', '+256 701 890123', 'contact@hoimaoil.ug', '801890123456'),
            ('Masindi Civil Contractors', 'Jane Nabukenya', 'Main Street, Masindi', '+256 701 901234', 'info@masindicivil.ug', '801901234567'),
            ('Mityana Construction Group', 'Daniel Lubwama', 'Mubende Road, Mityana', '+256 701 012345', 'sales@mityanaconst.ug', '801012345678'),
            ('Wakiso Developers Ltd', 'Susan Nakiganda', 'Entebbe Road, Wakiso', '+256 702 123456', 'info@wakisodev.ug', '802123456789'),
            ('Mukono Real Estate', 'George Kiwanuka', 'Jinja Road, Mukono', '+256 702 234567', 'contact@mukonorealestate.ug', '802234567890'),
            ('Ntungamo Builders Co', 'Patience Mugisha', 'Mbarara Road, Ntungamo', '+256 702 345678', 'info@ntungamobuilders.ug', '802345678901'),
            ('Rukungiri Infrastructure', 'Moses Tumwesigye', 'Kabale Road, Rukungiri', '+256 702 456789', 'sales@rukungiriinfra.ug', '802456789012'),
            ('Kanungu Engineering Services', 'Grace Kiconco', 'Kisoro Road, Kanungu', '+256 702 567890', 'info@kanungueng.ug', '802567890123'),
            ('Bundibugyo Construction', 'Samson Mumbere', 'Fort Portal Road, Bundibugyo', '+256 702 678901', 'contact@bundibugyoconst.ug', '802678901234'),
            ('Kamwenge Materials Supply', 'Joyce Akankwasa', 'Mbarara Road, Kamwenge', '+256 702 789012', 'info@kamwengematerials.ug', '802789012345'),
            ('Kyenjojo Builders', 'Patrick Busingye', 'Fort Portal Road, Kyenjojo', '+256 702 890123', 'sales@kyenjojobuilders.ug', '802890123456'),
            ('Kabarole Projects Ltd', 'Ruth Nyakaisiki', 'Mountain Road, Kabarole', '+256 702 901234', 'info@kabaroleprojects.ug', '802901234567'),
            ('Ntoroko Development Co', 'Francis Mugume', 'Kasese Road, Ntoroko', '+256 702 012345', 'contact@ntorokodev.ug', '802012345678'),
        ]

        sample_types = ['Soil', 'Concrete', 'Steel', 'Rocks', 'Water']
        sample_conditions = ['good', 'good', 'good', 'damaged', 'insufficient']  # Mostly good
        priorities = ['normal', 'normal', 'normal', 'urgent', 'rush']
        # More samples in active states (results expected soon)
        statuses = ['received', 'in_progress', 'in_progress', 'testing', 'testing', 'completed', 'completed', 'reported']
        delivery_methods = ['Walk-in', 'Courier', 'Hand delivery', 'Company vehicle']
        
        # Realistic quantities by sample type
        quantity_by_type = {
            'Soil': ['{q} kg', '{q} kg', '{q} kg', '{q} kg', '{q} kg', '{q} bags (25kg each)'],
            'Concrete': ['{q} cubes', '{q} cubes', '{q} cubes', '{q} cores', '{q} beams', '{q} specimens'],
            'Steel': ['{q} bars', '{q} bars', '{q} pieces', '{q} specimens', '{q} samples'],
            'Rocks': ['{q} kg', '{q} kg', '{q} pieces', '{q} samples'],
            'Water': ['{q} liters', '{q} liters', '{q} bottles (500ml)', '{q} bottles (1L)'],
        }
        
        locations = [
            'Kampala Central', 'Industrial Area, Kampala', 'Entebbe Road', 'Bwaise, Kampala',
            'Ntinda, Kampala', 'Najjera, Kampala', 'Lubowa, Kampala', 'Kira Town',
            'Jinja Road Construction Site', 'Mukono Industrial Park', 'Entebbe Airport Expansion',
            'Mbarara Road Upgrade', 'Masaka Highway Project', 'Gulu Northern Bypass',
            'Tororo Border Post', 'Hoima Oil Refinery Site', 'Kasese Mining Area'
        ]

        descriptions = {
            'Soil': [
                'Subgrade soil sample from road construction site',
                'Foundation soil for building construction',
                'Topsoil sample for agricultural assessment',
                'Lateritic soil from excavation site',
                'Clay soil sample for brick making',
                'Sandy soil for concrete mix design',
                'Compacted soil for embankment construction',
            ],
            'Concrete': [
                '28-day concrete cube samples for compressive strength',
                'Concrete core sample from existing structure',
                'Fresh concrete mix for slump test',
                'Concrete beam sample for flexural strength',
                'Precast concrete block samples',
                'Ready-mix concrete sample',
                'Reinforced concrete column sample',
            ],
            'Steel': [
                'Reinforcement bars for tensile strength testing',
                'Steel beam samples for structural analysis',
                'Welded steel joint samples',
                'Steel plate samples for quality control',
                'Rebar samples from construction site',
                'Steel pipe samples for pressure testing',
            ],
            'Rocks': [
                'Granite rock samples for aggregate testing',
                'Limestone samples for cement production',
                'Basalt rock for road construction',
                'Quarry rock samples for quality assessment',
                'Crushed stone samples for concrete aggregate',
            ],
            'Water': [
                'Borehole water sample for quality analysis',
                'Surface water from construction site',
                'Drinking water quality testing',
                'Wastewater sample for treatment assessment',
            ],
        }

        # Get users by role
        directors = list(User.objects.filter(role='director'))
        lab_managers = list(User.objects.filter(role='lab_manager'))
        office_staff = list(User.objects.filter(role='office_staff'))
        technicians = list(User.objects.filter(role='technician'))
        
        all_users = directors + lab_managers + office_staff + technicians
        
        if not all_users:
            self.stdout.write(self.style.ERROR('No users found in the system. Please create users first.'))
            return

        # Get active test items
        test_items = list(TestItem.objects.filter(is_active=True))
        
        if not test_items:
            self.stdout.write(self.style.ERROR('No active test items found. Please add test items first.'))
            return

        self.stdout.write(self.style.SUCCESS('Creating 30 Ugandan clients...'))
        
        # Create clients
        clients = []
        for name, contact, address, phone, email, reg_num in ugandan_companies:
            client, created = Client.objects.get_or_create(
                name=name,
                defaults={
                    'contact_person': contact,
                    'address': address,
                    'phone': phone,
                    'email': email,
                    'company_registration': reg_num,
                    'is_active': True,
                }
            )
            clients.append(client)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(clients)} clients.'))

        self.stdout.write(self.style.SUCCESS('Creating 40 samples...'))

        # Create 40 samples
        samples_created = 0
        for i in range(40):
            # Select random client
            client = random.choice(clients)
            
            # Select sample type and description
            sample_type = random.choice(sample_types)
            sample_desc = random.choice(descriptions.get(sample_type, ['Sample for testing']))
            
            # Select random user based on role (distribute evenly)
            if i < 10:
                received_by = random.choice(directors if directors else all_users)
            elif i < 20:
                received_by = random.choice(lab_managers if lab_managers else all_users)
            elif i < 30:
                received_by = random.choice(office_staff if office_staff else all_users)
            else:
                received_by = random.choice(technicians if technicians else all_users)
            
            # Random date within last week (0-7 days ago)
            days_ago = random.randint(0, 7)
            received_date = timezone.now() - timedelta(days=days_ago)
            collection_date = received_date.date() - timedelta(days=random.randint(0, 2))
            
            # Generate realistic quantity for sample type
            quantity_templates = quantity_by_type.get(sample_type, ['{q} samples'])
            quantity_template = random.choice(quantity_templates)
            if sample_type == 'Concrete':
                quantity_value = random.randint(3, 12)
            elif sample_type == 'Water':
                quantity_value = random.randint(2, 10)
            else:
                quantity_value = random.randint(5, 50)
            quantity = quantity_template.format(q=quantity_value)
            
            # Create sample
            sample = Sample.objects.create(
                client=client,
                sample_type=sample_type,
                sample_description=sample_desc,
                sample_condition=random.choice(sample_conditions),
                quantity=quantity,
                location_collected=random.choice(locations),
                collection_date=collection_date,
                received_by=received_by,
                received_date=received_date,
                priority=random.choice(priorities),
                status=random.choice(statuses),
                delivery_method=random.choice(delivery_methods),
                notes=f'Sample received from {client.name} for quality assurance testing.',
            )
            
            # Add 1-4 random tests to each sample
            num_tests = random.randint(1, 4)
            selected_tests = random.sample(test_items, min(num_tests, len(test_items)))
            
            for test_item in selected_tests:
                SampleTest.objects.create(
                    sample=sample,
                    test_item=test_item,
                    quantity_requested=random.randint(1, 3),
                    special_requirements='' if random.random() > 0.3 else 'Please follow standard testing protocol.',
                )
            
            # Create initial status history
            SampleStatusHistory.objects.create(
                sample=sample,
                new_status=sample.status,
                changed_by=received_by,
                notes=f'Sample received and entered into system by {received_by.get_full_name() or received_by.username}',
            )
            
            samples_created += 1
            
            if (i + 1) % 10 == 0:
                self.stdout.write(f'Created {i + 1} samples...')

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully created:\n'
            f'  - {len(clients)} clients\n'
            f'  - {samples_created} samples\n'
            f'  - Sample tests distributed across samples\n'
            f'  - Status history entries created'
        ))

