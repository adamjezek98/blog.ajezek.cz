from __future__ import absolute_import, unicode_literals

from django.db import models
from django.template.defaultfilters import slugify

from wagtail.wagtailcore import blocks
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailcore.fields import StreamField, RichTextField

from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel, StreamFieldPanel

from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailimages.blocks import ImageChooserBlock

from wagtail.wagtailsearch import index

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase, Tag

import operator

class HomePage(Page):
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('body', classname="full"),
    ]

    def get_posts_tags(self, homepage=None):

        if not homepage:
            homepage = self
        blogpages = homepage.get_children().live().order_by('-first_published_at')
        alltags = {}
        for page in blogpages:
            for tag in page.specific.get_tags():
                if tag in alltags.keys():
                    alltags[tag] += 1
                else:
                    alltags[tag] = 1
        tagsdict = {}
        sortedtags = sorted(alltags.items(), key=operator.itemgetter(1))
        sortedtags.reverse()
        print(sortedtags)
        return sortedtags
        for sortedtag in sortedtags:
            tagsdict[sortedtag[0]] = tagsdict[sortedtag[1]]

        return tagsdict


    def get_context(self, request):
        context = super(HomePage, self).get_context(request)
        context["blogpages_tags"] = self.get_posts_tags()
        if request.GET.get('tag'):
            tag = request.GET.get('tag')
            blogpages = BlogPage.objects.filter(tags__name=tag)
            context['blogpages'] = blogpages
            return context
        else:
            blogpages = self.get_children().live().order_by('-first_published_at')
            context['blogpages'] = blogpages
            return context


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey('BlogPage', related_name='tagged_items')


class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)

    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('date'),
            FieldPanel('tags'),
        ], heading="Blog information"),
        FieldPanel('intro'),
        StreamFieldPanel('body'),
        InlinePanel('gallery_images', label="Gallery images"),

    ]

    def get_posts_tags(self):
        homePage = HomePage()
        return homePage.get_posts_tags(homepage=self.get_parent())

    def get_tags(self):
        if self.tags.all().count():
            tags = []
            for tag in self.tags.all().values_list():
                if tag[1] != "none":
                    tags.append(tag[1])
            return tags
        else:
            return []

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    def save(self, *args, **kwargs):
        if not self.id:
            # Only set the slug when the object is created.
            self.slug = slugify(str(self.date) + "-" + self.title)
        super(BlogPage, self).save(*args, **kwargs)


class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]
