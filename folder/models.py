from django.urls import reverse

from django.db import models

from account.models import Account


class Folder(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        full_name = f'{self.name}'
        if self.parent:
            full_name = f'{self.parent}::' + full_name
        return full_name

    @property
    def depth(self):
        if not self.parent:
            return 0
        else:
            return self.parent.depth + 1

    @property
    def get_list_url(self):
        return reverse('folder:folder_list')

    def parent_url(self):
        url_list = []
        temp = self
        while(temp.parent):
            temp = temp.parent
            url_list.append(reverse('folder:folder_list') + '?id=' + str(temp.pk))

        return url_list
