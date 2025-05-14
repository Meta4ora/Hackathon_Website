from django.db import models

class PublicEvent(models.Model):
    id_event = models.IntegerField(primary_key=True)  # Matches 'id_event'
    event_name = models.CharField(max_length=255)     # Matches 'event_name'
    start_date = models.DateField()                   # Matches 'start_date'
    end_date = models.DateField()                     # Matches 'end_date'
    venue_name = models.TextField()                   # Matches 'venue_name'
    venue_location = models.TextField()               # Matches 'venue_location'

    class Meta:
        managed = False  # Django won't manage this table (since it's a view)
        db_table = 'eventdetailsview'  # Name of the database view

    def __str__(self):
        return self.event_name