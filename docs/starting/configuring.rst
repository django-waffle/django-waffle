.. _starting-configuring:

==================
Configuring Waffle
==================

There are a few global settings you can define to adjust Waffle's
behavior.

``WAFFLE_COOKIE``
    The format for the cookies Waffle sets. Must contain ``%s``.
    Defaults to ``dwf_%s``.

``WAFFLE_TEST_COOKIE``
    The format for the cookies Waffle sets for user testing. Must contain ``%s``.
    Defaults to ``dwft_%s``.

``WAFFLE_FLAG_DEFAULT``
    When a Flag is undefined in the database, Waffle considers it
    ``False``.  Set this to ``True`` to make Waffle consider undefined
    flags ``True``.  Defaults to ``False``.

``WAFFLE_FLAG_MODEL``
    The model that will be use to keep track of flags. Defaults to ``waffle.Flag``
    which allows user- and group-based flags. Can be swapped for a different Flag model
    that allows flagging based on other things, such as an organization or a company
    that a user belongs to. Analogous functionality to Django's extendable User models.
    Needs to be set at the start of a project, as the Django migrations framework does not
    support changing swappable models after the initial migration.

``WAFFLE_SWITCH_MODEL``
    The Django model that will be used for switches. Defaults to ``waffle.Switch``, which
    provides basic switch functionality. This can be swapped for a custom Switch model if
    additional fields or behaviors are needed. The custom model must inherit from
    ``waffle.models.AbstractBaseSwitch``. Needs to be set at the start of a project, as
    Django’s migration framework does not support changing swappable models after the
    initial migration.

``WAFFLE_SAMPLE_MODEL``
    The Django model that will be used for samples. Defaults to ``waffle.Sample``, which
    provides basic sample functionality. This can be swapped for a custom Sample model if
    additional fields or behaviors are needed. The custom model must inherit from
    ``waffle.models.AbstractBaseSample``. Needs to be set at the start of a project, as
    Django’s migration framework does not support changing swappable models after the
    initial migration.

``WAFFLE_SWITCH_DEFAULT``
    When a Switch is undefined in the database, Waffle considers it
    ``False``.  Set this to ``True`` to make Waffle consider undefined
    switches ``True``.  Defaults to ``False``.

``WAFFLE_SAMPLE_DEFAULT``
    When a Sample is undefined in the database, Waffle considers it
    ``False``.  Set this to ``True`` to make Waffle consider undefined
    samples ``True``.  Defaults to ``False``.

``WAFFLE_MAX_AGE``
    How long should Waffle cookies last? (Integer, in seconds.) Defaults
    to ``2529000`` (one month).

``WAFFLE_READ_FROM_WRITE_DB``
    When calling ``*_is_active`` methods, Waffle attempts to retrieve a cached
    version of the object, falling back to the database if necessary. In high-
    traffic scenarios with multiple databases (e.g. a primary being replicated
    to a readonly pool) this introduces the risk that a stale version of the
    object might be cached if one of these methods is called immediately after
    an update. Set this to ``True`` to ensure Waffle always reads Flags,
    Switches, and Samples from the DB configured for writes on cache misses.

``WAFFLE_OVERRIDE``
    Allow *all* Flags to be controlled via the querystring (to allow
    e.g. Selenium to control their behavior). Defaults to ``False``.

``WAFFLE_SECURE``
    Whether to set the ``secure`` flag on cookies. Defaults to ``True``.

``WAFFLE_CACHE_PREFIX``
    Waffle tries to store objects in cache pretty aggressively. If you
    ever upgrade and change the shape of the objects (for example
    upgrading from <0.7.5 to >0.7.5) you'll want to set this to
    something other than ``'waffle:'``. If you're using memcached this should
    be ASCII only, as that's all it supports.

``WAFFLE_CACHE_NAME``
    Which cache to use. Defaults to ``'default'``.

``WAFFLE_CREATE_MISSING_FLAGS``
    If Waffle encounters a reference to a flag that is not in the database, should Waffle create the flag?
    If true new flags are created and set to the value of ``WAFFLE_FLAG_DEFAULT``
    Defaults to ``False``.

``WAFFLE_CREATE_MISSING_SWITCHES``
    If Waffle encounters a reference to a switch that is not in the database, should Waffle create the switch?
    If true new switches are created and set to the value of ``WAFFLE_SWITCH_DEFAULT``
    Defaults to ``False``.

``WAFFLE_CREATE_MISSING_SAMPLES``
    If Waffle encounters a reference to a sample that is not in the database, should Waffle create the sample?
    If true new samples are created and set to the value of ``WAFFLE_SAMPLE_DEFAULT``
    Defaults to ``False``.

``WAFFLE_LOG_MISSING_FLAGS``
    If Waffle encounters a reference to a flag that is not in the database, should Waffle log it?
    The value describes the level of wanted warning, possible values are all levels know by pythons default logging,
    e.g. ``logging.WARNING``.
    Defaults to ``None``.

``WAFFLE_LOG_MISSING_SWITCHES``
    If Waffle encounters a reference to a switch that is not in the database, should Waffle log it?
    The value describes the level of wanted warning, possible values are all levels know by pythons default logging,
    e.g. ``logging.WARNING``.
    Defaults to ``None``.

``WAFFLE_LOG_MISSING_SAMPLES``
    If Waffle encounters a reference to a sample that is not in the database,, should Waffle log it?
    The value describes the level of wanted warning, possible values are all levels know by pythons default logging,
    e.g. ``logging.WARNING``.
    Defaults to ``None``.


``WAFFLE_ENABLE_ADMIN_PAGES``
    Enables the default admin pages for Waffle models. This is True by default,
    but can be disabled to override or customize the pages.

``WAFFLE_CACHE_FAILOVER``
    Whether to failover to the database in the event of an exception trying
    to perform a cache operation. Defaults to ``True``.

``WAFFLE_CACHE_RETRIES``
    Number of retry attempts after a failed cache operation, before failing
    over to the database. Defaults to ``0``.
