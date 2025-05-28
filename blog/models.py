from django.db import models

class PublicEvent(models.Model):
    id_event = models.IntegerField(primary_key=True)
    event_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    venue_name = models.TextField()
    venue_location = models.TextField()

    class Meta:
        managed = False
        db_table = 'eventdetailsview'

    def __str__(self):
        return self.event_name