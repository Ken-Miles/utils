.. currentmodule:: src

****************
API Reference
****************

The following section outlines the Subclasses contained in the Utils library and their respective methods.

.. _ext_commands_api_bot:

***********************
Main Library Subclasses
***********************

Bot Subclasses
===============

BotU
-------

.. attributetable:: src.bot.BotU

.. autoclass:: src.bot.BotU
    :members:
    :exclude-members: before_identify_hook
    :show-inheritance:

Context Subclasses
====================

ContextU
-------------

.. attributetable:: src.context.ContextU

.. autoclass:: src.context.ContextU
    :members:
    :exclude-members: after_invoke, before_invoke, check, check_once, command, event, group, hybrid_command, hybrid_group, listen
    :show-inheritance:

.. note::
    The following subclasses are used to represent the context of a command/event in a specific environment (e.g. Guild, DM).
    No code changes are made, only changes related to typing.

GuildContextU
-----------------

.. attributetable:: src.context.GuildContextU

.. autoclass:: src.context.GuildContextU
    :members:
    :exclude-members: after_invoke, before_invoke, check, check_once, command, event, group, hybrid_command, hybrid_group, listen
    :show-inheritance:

DMContextU
----------------

.. attributetable:: src.context.DMContextU

.. autoclass:: src.context.DMContextU
    :members:
    :exclude-members: after_invoke, before_invoke, check, check_once, command, event, group, hybrid_command, hybrid_group, listen
    :show-inheritance:

Cog Subclasses
================

CogU
-------

.. attributetable:: src.cog.CogU

.. autoclass:: src.cog.CogU
    :members: _get, _post, _put, _patch, _delete,  get_command_mention
    
    :show-inheritance:

Command Subclasses
====================

CommandU
--------------

.. attributetable:: src.command.CommandU

.. autoclass:: src.command.CommandU
    :members:
    :exclude-members: invoke
    :show-inheritance:

GroupU
----------

.. attributetable:: src.command.GroupU

.. autoclass:: src.command.GroupU
    :members:
    :exclude-members: invoke
    :show-inheritance:

HybridCommandU
---------------------

.. attributetable:: src.command.HybridCommandU

.. autoclass:: src.command.HybridCommandU
    :members:
    :exclude-members: invoke
    :show-inheritance:

HybridGroupU
------------------

.. attributetable:: src.command.HybridGroupU

.. autoclass:: src.command.HybridGroupU
    :members:
    :exclude-members: invoke
    :show-inheritance:

Converter Subclasses
=====================

MemberID
--------------

.. attributetable:: src.converters.MemberID

.. autoclass:: src.converters.MemberID
    :members:
    :exclude-members: convert
    :show-inheritance:

BannedMember
-------------------

.. attributetable:: src.converters.BannedMember

.. autoclass:: src.converters.BannedMember
    :members:
    :exclude-members: convert
    :show-inheritance:

EmojiConverter
-------------------

.. attributetable:: src.converters.EmojiConverter

.. autoclass:: src.converters.EmojiConverter
    :members:
    :exclude-members: convert
    :show-inheritance:

Custom Enums
==============

RequestType
----------------

This isn't perfect, but has the types of Request used in this library.

.. class:: src.enums.RequestType

    Specifies the type of web request.

    .. attribute:: GET

        Represents a GET request.
    
    .. attribute:: POST
            
        Represents a POST request.
    
    .. attribute:: PUT
                
        Represents a PUT request.

    .. attribute:: PATCH
     
        Represents a PATCH request.

    .. attribute:: DELETE

        Represents a DELETE request.    

    .. automethod:: src.enums.RequestType.get_method_callable

IntegrationType
--------------------

.. attributetable:: src.enums.IntegrationType

.. class:: src.enums.IntegrationType

    Specifies the type of integration.

    This class has the __int__ method defined to convert the IntegrationType to an integer.

    .. attribute:: guild

        Represents a Guild integration type. Represented by a ``0``.
    
    .. attribute:: user

        Represents a User integration. Represented by a ``1``.
    

Paginators
============

Special thanks to the following original code author for the Paginator classes:\n
-> @soheab on Discord (150665783268212746)

All additional modifications and improvements are made by the author of this library, `Ken-Miles <https://github.com/Ken-Miles>`_.

Classes
-----------

BaseButtonPaginator
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: src.paginator.BaseButtonPaginator
    :members:

ButtonPaginator
^^^^^^^^^^^^^^^^

.. autoclass:: src.paginator.ButtonPaginator
    :members:

FiveButtonPaginator
^^^^^^^^^^^^^^^^^^^^
.. autoclass:: src.paginator.FiveButtonPaginator
    :members:
    :show-inheritance:

Methods
-----------

generate_pages
^^^^^^^^^^^^^^^^
.. automethod:: src.paginator.generate_pages

create_paginator
^^^^^^^^^^^^^^^^
.. automethod:: src.paginator.create_paginator

Modals and Buttons
-----------------------

GoToPageModal
^^^^^^^^^^^^^^^^
.. autoclass:: src.paginator.GoToPageModal
    :members:
    :show-inheritance:

GoToPageButton
^^^^^^^^^^^^^^^^
.. autoclass:: src.paginator.GoToPageButton
    :members:
    :show-inheritance:

***************
Other Utilities
***************

Embed-related methods
=======================

.. automethod:: src.methods.makeembed

.. automethod:: src.methods.makeembed_bot

.. automethod:: src.methods.makeembed_failedaction

.. automethod:: src.methods.makeembed_successfulaction

.. automethod:: src.methods.makeembed_partialaction

Formatting methods
====================

dctimestamp
----------------------
.. automethod:: src.methods.dctimestamp

dchyperlink
---------------
.. automethod:: src.methods.dchyperlink

create_codeblock
----------------------
.. automethod:: src.methods.create_codeblock

Autocomplete methods
=======================

generic_autocomplete
--------------------------
.. automethod:: src.methods.generic_autocomplete

Miscellaneous
============================

merge_permissions
----------------------
.. automethod:: src.methods.merge_permissions

generate_transaction_id
------------------------------
.. automethod:: src.methods.generate_transaction_id

oauth_url
-------------
.. automethod:: src.methods.oauth_url

get_max_file_upload_limit
--------------------------------
.. automethod:: src.methods.get_max_file_upload_limit
