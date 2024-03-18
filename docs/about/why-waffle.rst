.. _about-why-waffle:

===========
Why Waffle?
===========

`Feature flags`_ are a critical tool for continuously integrating and
deploying applications. Waffle is one of `several options`_ for managing
feature flags in Django applications.

Waffle :ref:`aims to <about-goals>`

- provide a simple, intuitive API everywhere in your application;
- cover common use cases with batteries-included;
- be simple to install and manage;
- be fast and robust enough to use in production; and
- minimize dependencies and complexity.

Waffle has an `active community`_ and gets `fairly steady updates`_.


vs Gargoyle
===========

The other major, active feature flag tool for Django is Disqus's
Gargoyle_. Both support similar features, though Gargoyle offers more
options for building custom segments in exchange for some more
complexity and requirements.


Waffle in Production
====================

Despite its pre-1.0 version number, Waffle has been used in production
for years at places like Mozilla, Yipit and TodaysMeet.

- Mozilla (Support, MDN, Addons, etc)
- TodaysMeet
- Yipit

(If you're using Waffle in production and don't mind being included
here, let me know or add yourself in a pull request!)


.. _Feature flags: http://code.flickr.net/2009/12/02/flipping-out/
.. _several options: https://www.djangopackages.com/grids/g/feature-flip/
.. _active community: https://github.com/jazzband/django-waffle/graphs/contributors
.. _fairly steady updates: https://github.com/jazzband/django-waffle/pulse/monthly
.. _Gargoyle: https://github.com/disqus/gargoyle
