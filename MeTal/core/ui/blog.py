from core import (auth, mgmt, utils, cms, ui_mgr)
from core.cms import job_type
from core.log import logger
from core.menu import generate_menu, colsets, icons
from core.error import EmptyQueueError
from core.search import blog_search_results
from .ui import search_context, submission_fields, status_badge, save_action

from core.models import (Struct, get_site, get_blog, get_media,
    template_tags, Page, Blog, Queue, Template, Theme, get_theme,
    Category, PageCategory, MediaAssociation,
    TemplateMapping, Media, queue_jobs_waiting,
    Tag, template_type, publishing_mode, get_default_theme)

from core.models.transaction import transaction

from core.libs.bottle import (template, request, response, redirect)

from settings import (BASE_URL)

import datetime
from os import remove as _remove
from core.models import TagAssociation
from core.models import MediaAssociation

@transaction
def blog(blog_id, errormsg=None):
    '''
    UI for listing contents of a given blog
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_member(user, blog)

    try:
        pages_searched, search = blog_search_results(request, blog)
    except (KeyError, ValueError):
        pages_searched, search = None, None

    tags = template_tags(blog_id=blog.id,
        search=search,
        user=user)

    taglist = tags.blog.pages(pages_searched)

    paginator, rowset = utils.generate_paginator(taglist, request)

    tags.status = errormsg if errormsg is not None else None

    action = utils.action_button(
        'Create new page',
        '{}/blog/{}/newpage'.format(BASE_URL, blog.id)
        )

    # theme_actions = blog.theme_actions().menus()


    list_actions = [
        ['Republish', '{}/api/1/republish'],
        ]

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['blog'], blog),
        menu=generate_menu('blog_menu', blog),
        rowset=rowset,
        colset=colsets['blog'],
        icons=icons,
        action=action,
        list_actions=list_actions,
        **tags.__dict__)

    return tpl

@transaction
def blog_create(site_id):

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)

    new_blog = Blog(
        name="",
        description="",
        url="",
        path="")

    tags = template_tags(site_id=site.id,
        user=user)

    tags.blog = new_blog
    from core.libs import pytz

    themes = Theme.select()

    tpl = template('ui/ui_blog_settings',
        section_title="Create new blog",
        search_context=(search_context['sites'], None),
        menu=generate_menu('site_create_blog', site),
        nav_default='all',
        timezones=pytz.all_timezones,
        themes=themes,
        ** tags.__dict__
        )

    return tpl

@transaction
def blog_create_save(site_id):

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)

    errors = []

    new_blog = Blog(
            site=site,
            name=request.forms.getunicode('blog_name'),
            description=request.forms.getunicode('blog_description'),
            url=request.forms.getunicode('blog_url'),
            path=request.forms.getunicode('blog_path'),
            set_timezone=request.forms.getunicode('blog_timezone'),
            theme=get_default_theme(),
            )

    try:
        new_blog.validate()
    except Exception as e:
        errors.extend(e.args[0])

    if len(errors) == 0:
        from core.libs.peewee import IntegrityError
        try:
            new_blog.setup(user, new_blog.theme)
        except IntegrityError as e:
            from core.utils import field_error
            errors.append(field_error(e))

    if len(errors) > 0:

        status = utils.Status(
            type='danger',
            no_sure=True,
            message='The blog could not be created due to the following problems:',
            message_list=errors)
        from core.libs import pytz
        tags = template_tags(site=site,
            user=user)
        tags.status = status
        tags.blog = new_blog
        themes = Theme.select()
        tpl = template('ui/ui_blog_settings',
            section_title="Create new blog",
            search_context=(search_context['sites'], None),
            menu=generate_menu('site_create_blog', site),
            nav_default='all',
            themes=themes,
            timezones=pytz.all_timezones,
            ** tags.__dict__
            )
        return tpl

    else:
        # new_blog.setup(user, new_blog.theme)
        tags = template_tags(user=user, site=site,
            blog=new_blog)
        status = utils.Status(
            type='success',
            message='''
Blog <b>{}</b> was successfully created. You can <a href="{}/blog/{}/newpage">start posting</a> immediately.
'''.format(
                new_blog.for_display,
                BASE_URL, new_blog.id)
            )
        tags.status = status
        tpl = template('listing/report',
            search_context=(search_context['sites'], None),
            menu=generate_menu('site_create_blog', site),
            ** tags.__dict__
            )

        return tpl

# TODO: make this universal to create a user for both a blog and a site
# use ka
@transaction
def blog_create_user(blog_id):
    '''
    Creates a user and gives it certain permissions within the context of a given blog
    '''

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)
    tags = template_tags(blog_id=blog.id,
        user=user)

    edit_user = Struct()
    edit_user.name = ""
    edit_user.email = ""

    tpl = template('edit/edit_user_settings',
        section_title="Create new blog user",
        search_context=(search_context['sites'], None),
        edit_user=edit_user,
        **tags.__dict__
        )

    return tpl


@transaction
def blog_list_users(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)
    user_list = blog.users

    tags = template_tags(blog_id=blog.id,
        user=user)

    paginator, rowset = utils.generate_paginator(user_list, request)

    tpl = template('listing/listing_ui',
        section_title="List blog users",
        search_context=(search_context['sites'], None),
        menu=generate_menu('blog_list_users', blog),
        colset=colsets['blog_users'],
        paginator=paginator,
        rowset=rowset,
        user_list=user_list,
        **tags.__dict__)

    return tpl



@transaction
def blog_new_page(blog_id):
    '''
    Displays UI for newly created (unsaved) page
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_member(user, blog)

    tags = template_tags(
        blog_id=blog.id,
        user=user)

    tags.page = Page()

    referer = request.headers.get('Referer')
    if referer is None:
        referer = BASE_URL + "/blog/" + str(blog.id)

    blog_new_page = tags.page

    for n in submission_fields:
        blog_new_page.__setattr__(n, "")
        if n in request.query:
            blog_new_page.__setattr__(n, request.query.getunicode(n))

    blog_new_page.blog = blog_id
    blog_new_page.user = user
    blog_new_page.publication_date = datetime.datetime.utcnow()
    blog_new_page.basename = ''

    from core.cms import save_action_list

    from core.ui_kv import kv_ui
    kv_ui_data = kv_ui(blog_new_page.kvs())

    try:
        html_editor_settings = Template.get(
        Template.blog == blog,
        Template.title == 'HTML Editor Init',
        Template.template_type == template_type.system
        ).body
    except Template.DoesNotExist:
        from core.static import html_editor_settings

    tpl = template('edit/edit_page_ui',
        menu=generate_menu('create_page', blog),
        parent_path=referer,
        search_context=(search_context['blog'], blog),
        html_editor_settings=html_editor_settings,
        sidebar=ui_mgr.render_sidebar(
            panel_set='edit_page',
            status_badge=status_badge,
            save_action=save_action,
            save_action_list=save_action_list,
            kv_ui=kv_ui_data,
            **tags.__dict__),
        **tags.__dict__)

    return tpl

@transaction
def blog_new_page_save(blog_id):
    '''
    UI for saving a newly created page.
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_member(user, blog)

    tags = cms.save_page(None, user, blog)

    # TODO: move to model instance?
    logger.info("Page {} created by user {}.".format(
        tags.page.for_log,
        user.for_log))

    response.add_header('X-Redirect', BASE_URL + '/page/{}/edit'.format(str(tags.page.id)))

    return response

@transaction
def blog_media(blog_id):
    '''
    UI for listing media for a given blog
    '''

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_member(user, blog)

    media = blog.media.order_by(Media.id.desc())

    tags = template_tags(blog_id=blog.id,
        user=user)

    paginator, media_list = utils.generate_paginator(media, request)
    # media_list = media.paginate(paginator['page_num'], ITEMS_PER_PAGE)



    tpl = template('listing/listing_ui',
        paginator=paginator,
        media_list=media_list,
        menu=generate_menu('blog_manage_media', blog),
        icons=icons,
        search_context=(search_context['blog_media'], blog),
        rowset=media_list,
        colset=colsets['media'],

        **tags.__dict__)

    return tpl

@transaction
def blog_media_edit(blog_id, media_id, status=None):
    '''
    UI for editing a given media entry
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    is_member = auth.is_blog_member(user, blog)
    media = get_media(media_id, blog)
    permission = auth.is_media_owner(user, media)

    from core.ui_kv import kv_ui
    kv_ui_data = kv_ui(media.kvs(no_traverse=True))

    tags = template_tags(blog_id=blog.id,
         media=media,
         status=status,
         user=user,
        )
    tags.sidebar = ui_mgr.render_sidebar(
            panel_set='edit_media',
            status_badge=status_badge,
            # save_action_list=save_action_list,
            # save_action=save_action,
            kv_ui=kv_ui_data)

    return blog_media_edit_output(tags)

@transaction
def blog_media_edit_save(blog_id, media_id):
    '''
    Save changes to a media entry.
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    is_member = auth.is_blog_member(user, blog)
    media = get_media(media_id)
    permission = auth.is_media_owner(user, media)

    friendly_name = request.forms.getunicode('media_friendly_name')

    changes = False

    if friendly_name != media.friendly_name:
        changes = True
        media.friendly_name = friendly_name

    if changes is True:
        media.modified_date = datetime.datetime.utcnow()
        media.save()

        status = utils.Status(
            type='success',
            message='Changes to media <b>{}</b> saved successfully.'.format(
                media.for_display)
            )
    else:

        status = utils.Status(
            type='warning',
            no_sure=True,
            message='No discernible changes submitted for media <b>{}</b>.'.format(
                media.id, media.for_display)
            )

    logger.info("Media {} edited by user {}.".format(
        media.for_log,
        user.for_log))

    tags = template_tags(blog_id=blog.id,
         media=media,
         status=status,
         user=user)

    return blog_media_edit_output(tags)

def blog_media_edit_output(tags):

    tpl = template('edit/edit_media_ui',
        icons=icons,
        menu=generate_menu('blog_edit_media', tags.media),
        search_context=(search_context['blog_media'], tags.blog),
        **tags.__dict__)

    return tpl

# TODO: be able to process multiple media at once via a list
# using the list framework
# also allows for actions like de-associate, etc.
# any delete action that works with an attached asset, like a tag, should also behave this way
@transaction
def blog_media_delete(blog_id, media_id, confirm='N'):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    is_member = auth.is_blog_member(user, blog)
    media = get_media(media_id, blog)
    permission = auth.is_media_owner(user, media)

    tags = template_tags(blog_id=blog.id,
        media=media,
        user=user)

    report = []

    from core.utils import Status

    # if confirm == 'Y':
    if request.forms.getunicode('confirm') == user.logout_nonce:

        try:
            _remove(media.path)
        except:
            pass

        media.delete_instance(recursive=True,
            delete_nullable=True)

        confirmed = Struct()
        confirmed.message = 'Media {} successfully deleted'.format(
            media.for_log)
        confirmed.url = '{}/blog/{}/media'.format(BASE_URL, blog.id)
        confirmed.action = 'Return to the media listing'

        tags.status = Status(
            type='success',
            message=confirmed.message,
            action=confirmed.action,
            url=confirmed.url,
            close=False)

    else:
        s1 = ('You are about to delete media object <b>{}</b> from blog <b>{}</b>.'.format(
            media.for_display,
            blog.for_display))

        used_in = []

        for n in media.associated_with:
            used_in.append("<li>{}</li>".format(n.page.for_display))

        if len(used_in) > 0:
            s2 = ('''<p>Note that the following pages use this media object.
Deleting the object will remove it from these pages as well.
Any references to these images will show as broken.
<ul>{}</ul></p>
            '''.format(''.join(used_in)))
        else:
            s2 = '''
<p>This media object is not currently used in any pages.
However, if it is linked directly in a page without a media reference,
any such links will break. Proceed with caution.
'''

        yes = {
            'label':'Yes, delete this media',
            'id':'delete',
            'name':'confirm',
            'value':user.logout_nonce
            }
        no = {
            'label':'No, return to media properties',
            'url':'../{}/edit'.format(media.id)
            }

        tags.status = Status(
            type='warning',
            close=False,
            message=s1 + '<hr>' + s2,
            yes=yes,
            no=no
            )

    tpl = template('listing/report',
        menu=generate_menu('blog_delete_media', media),
        icons=icons,
        report=report,
        search_context=(search_context['blog_media'], blog),
        **tags.__dict__)

    return tpl

@transaction
def blog_categories(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_editor(user, blog)

    blog_category_list = blog.categories

    reason = auth.check_category_editing_lock(blog, True)

    tags = template_tags(blog_id=blog.id,
        user=user)

    tags.status = reason

    action = utils.action_button(
        'Add new category',
        '{}/blog/{}/newcategory'.format(BASE_URL, blog.id)
        )

    paginator, rowset = utils.generate_paginator(blog_category_list, request)

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['blog'], blog),
        menu=generate_menu('blog_manage_categories', blog),
        rowset=rowset,
        colset=colsets['categories'],
        icons=icons,
        action=action,
        **tags.__dict__)

    return tpl

@transaction
def blog_tags(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_author(user, blog)

    reason = auth.check_tag_editing_lock(blog, True)

    blog_tag_list = Tag.select().where(
        Tag.blog == blog).order_by(Tag.tag.asc())

    tags = template_tags(blog_id=blog.id,
        user=user)

    tags.status = reason

    paginator, rowset = utils.generate_paginator(blog_tag_list, request)

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['blog'], blog),
        menu=generate_menu('blog_manage_tags', blog),
        rowset=rowset,
        colset=colsets['tags'],
        icons=icons,
        **tags.__dict__)

    return tpl

@transaction
def blog_templates(blog_id):
    '''
    List all templates in a given blog
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_designer(user, blog)

    reason = auth.check_template_lock(blog, True)

    tags = template_tags(blog_id=blog.id,
        user=user)

    tags.status = reason

    from core.libs.peewee import JOIN_LEFT_OUTER

    template_list = Template.select(Template, TemplateMapping).join(
        TemplateMapping, JOIN_LEFT_OUTER).where(
        # (TemplateMapping.is_default == True) &
        (Template.blog == blog)
        ).order_by(Template.title)

    index_templates = template_list.select(Template, TemplateMapping).where(
        Template.template_type == template_type.index)

    page_templates = template_list.select(Template, TemplateMapping).where(
        Template.template_type == template_type.page)

    archive_templates = template_list.select(Template, TemplateMapping).where(
        Template.template_type == template_type.archive)

    template_includes = template_list.select(Template, TemplateMapping).where(
        Template.template_type == template_type.include)

    media_templates = template_list.select(Template, TemplateMapping).where(
        Template.template_type == template_type.media)

    system_templates = template_list.select(Template, TemplateMapping).where(
        Template.template_type == template_type.system)


    tags.list_items = [
        {'title':'Index Templates',
        'type': template_type.index,
        'data':index_templates},
        {'title':'Page Templates',
        'type': template_type.page,
        'data':page_templates},
        {'title':'Archive Templates',
        'type': template_type.archive,
        'data':archive_templates},
        {'title':'Includes',
        'type': template_type.include,
        'data':template_includes},
        {'title':'Media Templates',
        'type': template_type.media,
        'data':media_templates},
        {'title':'System Templates',
        'type': template_type.system,
        'data':system_templates},
        ]

    tpl = template('ui/ui_blog_templates',
        icons=icons,
        section_title="Templates",
        publishing_mode=publishing_mode,
        search_context=(search_context['blog_templates'], blog),
        menu=generate_menu('blog_manage_templates', blog),
        ** tags.__dict__)

    return tpl

@transaction
def blog_select_themes(blog_id):
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_designer(user, blog)
    reason = auth.check_template_lock(blog, True)

    themes = Theme.select().order_by(Theme.id)

    tags = template_tags(blog_id=blog.id,
        user=user)
    tags.status = reason

    paginator, rowset = utils.generate_paginator(themes, request)

    action = utils.action_button(
        'Save blog templates to new theme',
        '{}/blog/{}/theme/save'.format(BASE_URL, blog.id)
        )

    for n in rowset:
        n.blog = blog

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['blog'], blog),
        menu=generate_menu('blog_manage_themes', blog),
        rowset=rowset,
        colset=colsets['themes'],
        icons=icons,
        action=action,
        **tags.__dict__)

    return tpl


@transaction
def blog_republish(blog_id):
    '''
    UI for republishing an entire blog
    Eventually to be reworked
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)
    report = cms.republish_blog(blog_id)

    tpl = template('listing/report',
        report=report,
        search_context=(search_context['blog_queue'], blog),
        menu=generate_menu('blog_republish', blog),
        **template_tags(blog_id=blog.id,
            user=user).__dict__)

    return tpl

@transaction
def blog_purge(blog_id):
    '''
    UI for purging/republishing an entire blog
    Eventually to be reworked
    '''

    user = auth.is_logged_in(request)

    blog = get_blog(blog_id)

    permission = auth.is_blog_publisher(user, blog)

    report = cms.purge_blog(blog)

    tpl = template('listing/report',
        report=report,
        search_context=(search_context['blog'], blog),
        menu=generate_menu('blog_purge', blog),
        **template_tags(blog_id=blog.id,
            user=user).__dict__)

    return tpl

@transaction
def blog_queue(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)

    tags = template_tags(blog_id=blog.id,
            user=user)

    paginator, queue_list = utils.generate_paginator(tags.queue, request)

    tpl = template('queue/queue_ui',
        queue_list=queue_list,
        paginator=paginator,
        job_type=job_type.description,
        search_context=(search_context['blog_queue'], blog),
        menu=generate_menu('blog_queue', blog),
        **tags.__dict__)

    return tpl


@transaction
def blog_settings(blog_id, nav_setting):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)

    auth.check_settings_lock(blog)

    tags = template_tags(blog_id=blog.id,
        user=user)

    tags.nav_default = nav_setting

    return blog_settings_output(tags)

@transaction
def blog_settings_save(blog_id, nav_setting):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)

    _get = request.forms.getunicode

    blog.name = _get('blog_name', blog.name)
    blog.description = _get('blog_description', blog.description)
    blog.set_timezone = _get('blog_timezone')

    blog.url = _get('blog_url', blog.url)
    blog.path = _get('blog_path', blog.path)
    blog.base_extension = _get('blog_base_extension', blog.base_extension)
    blog.media_path = _get('blog_media_path', blog.media_path)

    from core.utils import Status
    from core.libs.peewee import IntegrityError
    errors = []

    try:
        blog.validate()
        blog.save()
    except IntegrityError as e:
        from core.utils import field_error
        errors.append(field_error(e))
    except Exception as e:
        errors.extend(e.args[0])

    if len(errors) > 0:

        status = Status(
            type='danger',
            no_sure=True,
            message='Blog settings could not be saved due to the following problems:',
            message_list=errors)
    else:
        status = Status(
            type='success',
            message="Settings for <b>{}</b> saved successfully.<hr/>It is recommended that you <a href='{}/blog/{}/purge'>republish this blog</a> immediately.".format(
                blog.for_display, BASE_URL, blog.id))

        logger.info("Settings for blog {} edited by user {}.".format(
            blog.for_log,
            user.for_log))

    tags = template_tags(blog_id=blog.id,
        user=user)

    tags.nav_default = nav_setting

    if status is not None:
        tags.status = status

    return blog_settings_output(tags)

def blog_settings_output(tags):
    from core.libs import pytz
    timezones = pytz.all_timezones
    path = '/blog/{}/settings/'.format(tags.blog.id)
    tpl = template('ui/ui_blog_settings',
        # section_title='Basic settings',
        search_context=(search_context['blog'], tags.blog),
        timezones=timezones,
        menu=generate_menu('blog_settings', tags.blog),
        nav_tabs=(
            ('basic', path + 'basic', 'Basic'),
            ('dirs', path + 'dirs', 'Directories')
            ),
        **tags.__dict__)

    return tpl


@transaction
def blog_publish(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)

    # TODO: check if control job already exists, if so, report back and quit

    '''
    queue = Queue.select().where(
        Queue.blog == blog.id,
        Queue.is_control == False)

    queue_length = queue.count()
    '''
    queue = Queue.select().where(
        Queue.blog == blog.id)

    queue_length = queue_jobs_waiting(blog=blog)

    tags = template_tags(blog_id=blog.id,
            user=user)

    if queue_length > 0:

        start_message = template('queue/queue_run_include',
            queue=queue,
            percentage_complete=0)

        try:
            Queue.get(Queue.site == blog.site,
                Queue.blog == blog,
                Queue.is_control == True)

        except Queue.DoesNotExist:

            cms.start_queue(blog=blog,
                queue_length=queue_length)

            '''
            cms.push_to_queue(blog=blog,
                site=blog.site,
                job_type=job_type.control,
                is_control=True,
                data_integer=queue_length
                )
            '''
    else:

        start_message = "Queue empty."

    tpl = template('queue/queue_run_ui',
        original_queue_length=queue_length,
        start_message=start_message,
        search_context=(search_context['blog_queue'], blog),
        menu=generate_menu('blog_queue', blog),
        **tags.__dict__)

    return tpl

@transaction
def blog_publish_progress(blog_id, original_queue_length):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)

    try:
        queue_count = cms.process_queue(blog)
    except EmptyQueueError:
        queue_count = 0
    except BaseException as e:
        raise e

    percentage_complete = int((1 - (int(queue_count) / int(original_queue_length))) * 100)

    tpl = template('queue/queue_run_include',
            queue_count=queue_count,
            percentage_complete=percentage_complete)

    return tpl

@transaction
def blog_publish_process(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)

    # queue_jobs_waiting should report actual JOBS
    # queue_control_jobs_waiting should report CONTROL JOBS
    # both should return a tuple of the actual queue and the queue count

    # get how many control jobs we have
    queue = Queue.select().where(Queue.blog == blog.id,
                Queue.is_control == True)

    queue_count = queue.count()
    if queue_count == 0:

        # get how many regular jobs we have
        queue = Queue.select().where(Queue.blog == blog_id,
                Queue.is_control == False)

        if queue.count() > 0:
            cms.start_queue(blog, queue_count)
            '''
            cms.push_to_queue(blog=blog,
                site=blog.site,
                job_type=job_type.control,
                is_control=True,
                data_integer=queue.count()
                )
            '''

            queue_count = cms.process_queue(blog)

    else:
        queue_count = cms.process_queue(blog)

    tpl = template('queue/queue_counter_include',
            queue_count=queue_count)

    return tpl


@transaction
def blog_save_theme(blog_id):
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)
    reason = auth.check_template_lock(blog)

    tags = template_tags(blog=blog,
            user=user)

    from core.utils import Status, create_basename_core

    if request.method == 'POST':

        theme = Theme(
            title=request.forms.getunicode('theme_title'),
            description=request.forms.getunicode('theme_description'),
            json='')

        export = blog.export_theme(theme.title, theme.description, user)

        from settings import THEME_FILE_PATH, _sep
        import os

        directory_name = create_basename_core(theme.title)
        dirs = [x[0] for x in os.walk(THEME_FILE_PATH)]
        dir_name_ext = 0
        dir_name_full = directory_name

        while 1:
            if dir_name_full in dirs:
                dir_name_ext += 1
                dir_name_full = directory_name + "-" + str(dir_name_ext)
                continue
            else:
                break

        dir_name_final = THEME_FILE_PATH + _sep + dir_name_full
        os.makedirs(dir_name_final)
        theme.json = dir_name_full
        theme.save()

        for n in export:
            with open(dir_name_final + _sep +
                n , "w", encoding='utf-8') as output_file:
                output_file.write(export[n])

        save_tpl = 'listing/report'
        status = Status(
            type='success',
            close=False,
            message='''
Theme <b>{}</b> was successfully saved from blog <b>{}</b>.
'''.format('', blog.for_display, ''),
            action='Return to theme list',
            url='{}/blog/{}/themes'.format(
                BASE_URL, blog.id)
            )
    else:

        save_tpl = 'edit/edit_theme_save'
        status = None

    tags.status = status if reason is None else reason

    tpl = template(save_tpl,
        menu=generate_menu('blog_save_theme', blog),
        search_context=(search_context['blog'], blog),
        theme_title=blog.theme.title + " (Revised {})".format(datetime.datetime.now()),
        theme_description=blog.theme.description,
        ** tags.__dict__)

    # TODO: also get theme description
    return tpl

@transaction
def blog_apply_theme(blog_id, theme_id):
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)
    reason = auth.check_template_lock(blog)

    theme = get_theme(theme_id)

    tags = template_tags(blog=blog,
            user=user)

    from core.utils import Status

    if request.forms.getunicode('confirm') == user.logout_nonce:

        from core.models import db
        with db.transaction() as txn:
            mgmt.theme_apply_to_blog(theme, blog, user)

        status = Status(
            type='success',
            close=False,
            message='''
Theme <b>{}</b> was successfully applied to blog <b>{}</b>.</p>
It is recommended that you <a href="{}">republish this blog.</a>
'''.format(theme.for_display, blog.for_display, '{}/blog/{}/republish'.format(
                BASE_URL, blog.id))
            )

    else:

        status = Status(
            type='warning',
            close=False,
            message='''
You are about to apply theme <b>{}</b> to blog <b>{}</b>.</p>
<p>This will OVERWRITE AND REMOVE ALL EXISTING TEMPLATES on this blog!</p>
'''.format(theme.for_display, blog.for_display),
            url='{}/blog/{}/themes'.format(
                BASE_URL, blog.id),
            yes={'id':'delete',
                'name':'confirm',
                'label':'Yes, I want to apply this theme',
                'value':user.logout_nonce},
            no={'label':'No, don\'t apply this theme',
                'url':'{}/blog/{}/themes'.format(
                BASE_URL, blog.id)}
            )

    tags.status = status if reason is None else reason

    tpl = template('listing/report',
        menu=generate_menu('blog_apply_theme', [blog, theme]),
        search_context=(search_context['blog'], blog),
        **tags.__dict__)

    return tpl


@transaction
def blog_import (blog_id):
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)
    reason = auth.check_template_lock(blog, True)

    tags = template_tags(blog=blog,
        user=user)

    import os, settings
    import_path = os.path.join(
        settings.APPLICATION_PATH,
        "data",
        "import.json")

    tags.status = reason

    if request.method == "POST":
        import json
        from core.utils import string_to_date

        import_path = request.forms.getunicode('import_path')
        with open(import_path, 'r', encoding='utf8') as f:
            json_data = json.load(f)

        q = []

        from core.models import KeyValue, page_status
        from core.cms import media_filetypes

        format_str = "<b>{}</b> / (<i>{}</i>)"

        for n in json_data:
            id = n['id']
            match = Page().kv_get('legacy_id', id)
            if match is not None:
                q.append("Exists: " + format_str.format(n['title'], id))
            else:
                q.append("Creating: " + format_str.format(n['title'], id))

                new_entry = Page()
                new_entry.title = n['title']
                new_entry.text = n['text']
                new_entry.basename = n['basename']
                new_entry.excerpt = n['excerpt']
                new_entry.user = user
                new_entry.blog = blog
                new_entry.created_date = string_to_date(n['created_date'])
                new_entry.publication_date = string_to_date(n['publication_date'])
                new_entry.modified_date = new_entry.publication_date

                if n['status'] in ('Publish', 'Published', 'Live'):
                    new_entry.status = page_status.published

                new_entry.save(user)

                # Register a legacy ID for the page

                new_entry.kv_set("legacy_id", n["id"])

                # Set default page category for blog

                saved_page_category = PageCategory.create(
                    page=new_entry,
                    category=blog.default_category,
                    primary=True)

                # Register tags

                tags_added, tags_existing = Tag.add_or_create(n['tags'], blog=blog)

                q.append('Tags added: {}'.format(','.join(tags_added)))
                q.append('Tags existing: {}'.format(','.join(tags_existing)))

                # Register KVs

                kvs = n['kvs']
                for key in kvs:
                    value = kvs[key]
                    new_entry.kv_set(key, value)
                    q.append('KV: {}:{}'.format(key, value))

                # Register media

                media = n['media']

                for m in media:

                    if 'path' not in m:
                        continue

                    path = os.path.split(m['path'])

                    new_media = Media(
                        filename=path[1],
                        path=m['path'],
                        url=m['url'],
                        type=media_filetypes.image,
                        created_date=string_to_date(m['created_date']),
                        modified_date=string_to_date(m['modified_date']),
                        friendly_name=m['friendly_name'],
                        user=user,
                        blog=blog,
                        site=blog.site
                        )

                    new_media.save()

                    media_association = MediaAssociation(
                        media=new_media,
                        page=new_entry)

                    media_association.save()

                    # Save legacy ID to KV on media

                    if 'id' in m:
                        new_media.kv_set('legacy_id', m['id'])

                    q.append('IMG: {}'.format(new_media.url))

                    # add tags for media

                    Tag.add_or_create(m['tags'], media=new_media)

                cms.build_pages_fileinfos((new_entry,))

        tpl = '<p>'.join(q)

        # todo: categories, special KVs, etc.

    else:
        tpl = template('ui/ui_blog_import',
            menu=generate_menu('blog_import', blog),
            search_context=(search_context['blog'], blog),
            import_path=import_path,
            **tags.__dict__)

    return tpl

