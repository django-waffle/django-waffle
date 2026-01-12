.. _testing-user:

========================
User testing with Waffle
========================

Testing a feature (i.e. not :ref:`testing the code <testing-automated>`)
with users usually takes one of two forms: small-scale tests with
individuals or known group, and large-scale tests with a subset of
production users. Waffle provides tools for the former and has some
suggestions for the latter.


Small-scale tests
=================

There are two ways to control a flag for an individual user:

- add their account to the flag's list of users, or
- use testing mode.

Querystring Parameter
---------------------

Testing mode makes it possible to enable a flag via a querystring
parameter (like ``WAFFLE_OVERRIDE``) but is unique for two reasons:

- it can be enabled and disabled on a flag-by-flag basis, and
- it only requires the querystring parameter once, then relies on
  cookies.

If the flag we're testing is called ``foo``, then we can enable testing
mode, and send users to ``oursite.com/testpage?dwft_foo=1`` (or ``=0``)
and the flag will be on (or off) for them for the remainder of their
session.

.. warning::

    Currently, the flag **must** be used by the first page they visit,
    or the cookie will not get set. See `#80`_ on GitHub.

Researchers can send a link with these parameters to anyone and then
observe or ask questions. At the end of their session, or when testing
mode is deactivated, they will call back to normal behavior.

For a small group, like a company or team, it may be worth creating a
Django group and adding or removing the group from the flag.

HTTP Header
-----------

In some cases, such as a backend API, it may be easier for a client to provide
an HTTP header instead of a querystring parameter.

When a flag, ``foo``, is in testing mode, simply provide the HTTP header
``DWFT-Foo: 1`` (or ``0``) to turn the flag on (or off).

This feature can also allow for a downstream service to make the decision of
enabling/disabling a flag, and then propagating that decision to other upstream
services, allowing for a more complete testing of more complex microservice
infrastructures.

Order of Precedence
-------------------

Since there are multiple controls to explicitly enable and disable flags in
testing mode, it's important to understand the order of precedence used to
determine when a flag is enabled/disabled when multiple controls are present at
once. If any one of these controls is present at all, the subsequent controls
will not be checked.

1. Querystring Parameter
2. HTTP Header
3. Cookie

Large-scale tests
=================

Large scale tests are tests along the lines of "roll this out to 5% of
users and observe the relevant metrics." Since "the relevant metrics"
is very difficult to define across all sites, here are some thoughts
from my experience with these sorts of tests.


Client-side metrics
-------------------

Google Analytics—and I imagine similar products—has the ability to
segment by page or `session variables`_. If you want to A/B test a
conversion rate or funnel, or otherwise measure the impact on some
client-side metric, using these variables is a solid way to go. For
example, in GA, you might do the following to A/B test a landing page:

.. code-block:: django

    ga('set', 'dimension1', 'Landing Page Version {% flag "new_landing_page" %}2{% else %}1{% endif %}');

Similarly you might set session or visitor variables for funnel tests.

The exact steps to both set a variable like this and then to create
segments and examine the data will depend on your client-side analytics
tool. And, of course, this can be combined with other data and further
segmented if you need to.


Server-side metrics
-------------------

I use StatsD_ religiously. Sometimes Waffle is useful for load and
capacity testing in which case I want to observe timing data or error
rates.

Sometimes, it makes sense to create entirely new metrics, and measure
them directly, e.g.::

    if flag_is_active('image-process-service'):
        with statsd.timer('imageservice'):
            try:
                processed = make_call_to_service(data)
            except ServiceError:
                statsd.incr('imageservice.error')
            else:
                statsd.incr('imageservice.success')
    else:
        with statsd.timer('process-image'):
            processed = do_inline_processing(data)

Other times, existing data—e.g. timers on the whole view—isn't going to
move. If you have enough data to be statistically meaningful, you can
measure the impact for a given proportion of traffic and derive the time
for the new code.

If a flag enabling a refactored codepath is set to 20% of users, and
average time has improved by 10%, you can calculate that you've improved
the speed by 50%!

You can use the following to figure out the average for requests using
the new code. Let :math:`t_{old}` be the average time with the flag at
0%, :math:`t_{total}` be the average time with the flag at :math:`p *
100%`. Then the average for requests using new code, :math:`t_{new}`
is...

.. math::

    t_{new} = t_{old} - \frac{t_{old} - t_{total}}{p}

If you believe my math (you should check it!) then you can measure the
average with the flag at 0% to get :math:`t_{old}` (let's say 1.2
seconds), then at :math:`p * 100` % (let's say 20%, so :math:`p = 0.2`)
to get :math:`t_{total}` (let's say 1.08 seconds, a 10% improvement) and
you have enough to get the average of the new path.

.. math::

    t_{new} = 1.2 - \frac{1.2 - 1.08}{0.2} = 0.6

Wow, good work!

You can use similar methods to derive the impact on other factors.


.. _session variables: https://support.google.com/analytics/answer/9191807?hl=en
.. _#80: https://github.com/django-waffle/django-waffle/issues/80
.. _StatsD: https://github.com/etsy/statsd
