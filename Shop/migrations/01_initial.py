
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Name', models.CharField(max_length=50)),
                ('Address', models.CharField(max_length=50)),
                ('Email', models.CharField(max_length=50)),
                ('Gender', models.CharField(max_length=10)),
                ('Date_of_Birth', models.IntegerField(max_length=20)),
            ],
        ),
    ]
