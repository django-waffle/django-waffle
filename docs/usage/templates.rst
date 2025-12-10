.. _usage-templates:
.. highlight:: django

=========================
Using Waffle in templates
=========================

Waffle makes it easy to test :ref:`flags <types-flag>`, :ref:`switches
<types-switch>`, and :ref:`samples <types-sample>` in templates to flip
features on the front-end. It includes support for both Django's
built-in templates and for Jinja2_.

.. warning::

    Before using samples in templates, see the warning in the
    :ref:`Sample chapter <types-sample>`.


.. _templates-django:

Django Templates
================

Load the ``waffle_tags`` template tags::

    {% load waffle_tags %}

In Django templates, Waffle provides three new block types, ``flag``,
``switch``, and ``sample``, that function like ``if`` blocks. Each block
supports an optional ``else`` to be rendered if the flag, switch, or
sample in inactive.


Flags
-----

::

    {% flag "flag_name" %}
        flag_name is active!
    {% else %}
        flag_name is inactive
    {% endflag %}


Switches
--------

::

    {% switch "switch_name" %}
        switch_name is active!
    {% else %}
        switch_name is inactive
    {% endswitch %}


Samples
-------

::

    {% sample "sample_name" %}
        sample_name is active!
    {% else %}
        sample_name is inactive
    {% endsample %}


Django Template Filters and Tags
================================
Django Waffle provides three new Django Template tags and filters, ``flag_is_active``,
``switch_is_active``, and ``sample_is_active``. Each of these tags and filters can be used in Django
template's if statement contitions to check if a flag, switch, or sample is active.

This is useful for when a django template context variable and a flag, switch, or sample are required to
be active in order to render a certain part of the template.

flag_is_active
--------------

::

    {% flag_is_active "flag" request True as is_flag_active %}
    {% if is_flag_active %}
        flag_is_active on
    {% else %}
        flag_is_active off
    {% endif %}

switch_is_active
----------------

::

    {% if "switch"|switch_is_active %}
        switch_is_active on
    {% else %}
        switch_is_active off
    {% endif %}

sample_is_active
----------------

::

    {% if "sample"|sample_is_active %}
        sample_is_active on
    {% else %}
        sample_is_active off
    {% endif %}



.. _templates-jinja:

Jinja Templates
===============

When used with Jinja2_, Waffle provides a ``waffle`` object in the Jinja
template context that can be used with normal ``if`` statements. Because
these are normal ``if`` statements, you can use ``else`` or ``if not``
as normal.


Flags
-----

::

    {% if waffle.flag('flag_name') %}
        flag_name is active!
    {% endif %}


Switches
--------

::

    {% if waffle.switch('switch_name') %}
        switch_name is active!
    {% endif %}


Samples
-------

::

    {% if waffle.sample('sample_name') %}
        sample_name is active!
    {% endif %}


.. _Jinja2: http://jinja.pocoo.org/
