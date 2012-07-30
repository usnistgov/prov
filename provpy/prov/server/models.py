'''Django app for the Provenance Web Service

Providing a REST API and a Web user interface for sending and retrieving
provenance graphs from a server 

@author: Trung Dong Huynh <trungdong@donggiang.com>
@copyright: University of Southampton 2012
'''

from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import  post_save, post_syncdb
from django.contrib.auth.signals import user_logged_in, user_logged_out
from tastypie.models import ApiKey
import logging, json
from prov.model import ProvBundle
from prov.persistence.models import PDBundle
logger = logging.getLogger(__name__)

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)


def _create_profile(sender, created, instance, **kwargs):
    if(created):
        UserProfile.objects.create(user=instance)
        instance.groups.add(Group.objects.get(name='public'))

def _create_public_group(**kwargs):
    from prov.settings import ANONYMOUS_USER_ID, PUBLIC_GROUP_ID
    try:
        public = Group.objects.get(name='public') 
    except Group.DoesNotExist:
        public = Group.objects.create(id=PUBLIC_GROUP_ID,name='public')
    try:
        User.objects.get(id=ANONYMOUS_USER_ID).groups.add(public)
    except User.DoesNotExist:
        User.objects.create(id=ANONYMOUS_USER_ID, username='AnonymousUser').groups.add(public)
 
post_save.connect(_create_profile, sender=User, dispatch_uid=__file__)
post_syncdb.connect(_create_public_group)

class   Container(models.Model):
    '''
    
    '''
    owner = models.ForeignKey(User, blank=True, null=True)
    content = models.ForeignKey(PDBundle, unique=True)
    public = models.BooleanField(default=False)
    
    class Meta:
        permissions = (
            ("view_container", "View the container."),
            ("admin_container", "Administrate permissions on the container."),
            ("ownership_container", "Changing ownership of the container."),
        )
    
    def delete(self):
        if self.content:
            self.content.delete()
        super(Container, self).delete()

    @staticmethod
    def create(rec_id, raw_json, owner, public=False):
        prov_bundle = ProvBundle();
        try:
            prov_bundle._decode_JSON_container(raw_json)
        except TypeError:
            prov_bundle = json.loads(raw_json, cls=ProvBundle.JSONDecoder)
        pdbundle = PDBundle.create(rec_id)
        pdbundle.save_bundle(prov_bundle)
        return Container.objects.create(owner=owner, content=pdbundle, public=public)