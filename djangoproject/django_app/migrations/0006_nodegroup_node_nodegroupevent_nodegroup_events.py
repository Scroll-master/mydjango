# Generated by Django 5.0.3 on 2024-04-28 18:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_app', '0005_event'),
    ]

    operations = [
        migrations.CreateModel(
            name='NodeGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('ip_address', models.CharField(max_length=15)),
                ('location', models.CharField(blank=True, max_length=128)),
                ('status', models.BooleanField(default=True)),
                ('group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='nodes', to='django_app.nodegroup')),
            ],
        ),
        migrations.CreateModel(
            name='NodeGroupEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_app.event')),
                ('node_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_app.nodegroup')),
            ],
            options={
                'db_table': 'nodegroup_event',
            },
        ),
        migrations.AddField(
            model_name='nodegroup',
            name='events',
            field=models.ManyToManyField(related_name='node_groups', through='django_app.NodeGroupEvent', to='django_app.event'),
        ),
    ]
