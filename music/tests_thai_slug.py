"""Regression tests for the Thai-only slug collision on Genre and Tag.

slugify() strips every Thai character, so a genre named "เพลงรัก" slugifies
to "". The slug column is unique, so the second Thai-only name used to raise
IntegrityError and the create page returned a 500. These tests pin the
fallback that mints a token slug when the slugified name comes back empty.
"""

import re

from django.test import TestCase

from music.models import Genre, Tag

THAI = "เพลงรักที่ใช้สำหรับทดสอบ"


class ThaiSlugTests(TestCase):
    def test_thai_only_genre_gets_a_non_empty_slug(self):
        genre = Genre.objects.create(name=THAI)
        self.assertTrue(genre.slug, "slug must not be empty for a Thai-only name")
        self.assertTrue(re.match(r"^g-[0-9a-f]{6}$", genre.slug), genre.slug)

    def test_thai_only_tag_gets_a_non_empty_slug(self):
        tag = Tag.objects.create(name=THAI)
        self.assertTrue(tag.slug, "slug must not be empty for a Thai-only name")
        self.assertTrue(re.match(r"^t-[0-9a-f]{6}$", tag.slug), tag.slug)

    def test_two_thai_only_genres_do_not_collide(self):
        first = Genre.objects.create(name=THAI + " ๑")
        second = Genre.objects.create(name=THAI + " ๒")
        self.assertNotEqual(first.slug, second.slug)
        self.assertEqual(Genre.objects.count(), 2)

    def test_two_thai_only_tags_do_not_collide(self):
        first = Tag.objects.create(name=THAI + " ๑")
        second = Tag.objects.create(name=THAI + " ๒")
        self.assertNotEqual(first.slug, second.slug)
        self.assertEqual(Tag.objects.count(), 2)

    def test_latin_name_still_gets_a_readable_slug(self):
        genre = Genre.objects.create(name="Love Songs")
        self.assertEqual(genre.slug, "love-songs")

    def test_editing_a_name_keeps_the_original_slug(self):
        genre = Genre.objects.create(name=THAI)
        original = genre.slug
        genre.name = THAI + " แก้ไขแล้ว"
        genre.save()
        genre.refresh_from_db()
        self.assertEqual(genre.slug, original)

    def test_thai_name_mixed_with_latin_uses_the_latin_part(self):
        genre = Genre.objects.create(name="Rock หนักแน่น")
        self.assertEqual(genre.slug, "rock")

    def test_creating_a_genre_through_the_form_mints_a_slug(self):
        from music.forms import GenreForm

        form = GenreForm({"name": THAI, "description": ""})
        self.assertTrue(form.is_valid(), form.errors)
        genre = form.save()
        self.assertTrue(genre.slug, genre.slug)

    def test_tag_form_mints_a_slug_for_thai_name(self):
        from music.forms import TagForm

        form = TagForm({"name": THAI})
        self.assertTrue(form.is_valid(), form.errors)
        tag = form.save()
        self.assertTrue(tag.slug, tag.slug)