# -*- coding: utf-8 -*-
#
#################################################################################
{
    'name': 'HC Simplify Access Management',
    'version': '14.0.1.1.0',
    'sequence': 5,
    'author': 'Hash Code IT Soultions',
    'license': 'OPL-1',
    'category': 'Extra Tools',
    'website': 'https://www.hashcodeit.com/',
    'summary': """All In One Access Management App for setting the correct access rights for fields, models, menus, views for any module and for any user.
        All in one access management App,
        Easier then Record rules setup,
        Centralize access rules,
        User wise access rules,
        Show only what is needed for users,
        Access rules setup,
        Easy access rights setup, Hide Any Menu, Any Field, Any Report, Any Button,
        Easy To Configure,
        Main Features:-
            Hide fields,
            Hide Buttons,
            Hide Tabs,
            Hide views,
            Hide Contacts,
            Hide Menus,
            Hide submenus,
            Hide sub-menus,
            Hide reports,
            Hide actions,
            Hide server actions,
            Hide import,
            Hide delete,
            Hide archive,
            Hide Tree view, 
            Hide Form view, 
            Hide Kanban view, 
            Hide Calendar view, 
            Hide Pivot,
            Hide Graph view,
            Hide Apps,
            Hide object buttons,
            Hide action buttons,
            Hide smart buttons,
            Readonly Any Field,
            read only user,
            readonly user,
            Hide create,
            Hide duplicate,
            Control every fields,
            Control every views,
            Control every buttons,
            Control every actions.
            Multi Company supported.
        """,
    'description': """
        All In One Access Management App for setting the correct access rights for fields, models, menus, views for any module and for any user.
        Configuring correct access rights in Odoo is quite technical for someone who has little experience with the system and can get messy if you are not sure what you are doing. This module helps you avoid all this complexity by providing you with a user friendly interface from where you can define access to specific objects in one place such as -

        Model/App access (Reports, Actions, Views, Readonly, Create, Write, Delete, Export, Archive etc.)
        Fields access (Invisible, Readonly fields for any model/app)
        Menu access(Hide any menu/submenu for any model/app for selected users)
        Views Access (Hide any view such as Tree view, Form view, Kanban view, Calendar view, Pivot & Graph view, etc)
        Hide Tabs and buttons
        Or, make any user Readonly
        Also the app allows you to create user-wise access management so that you can add/remove users to and from any group(s) in batch and with much ease.
        If you want to hide unwanted menu, sub-menu,fields,button(smart button and regular button), report action for any users, then you can use this app.
        
        All in one access management App,
        Easier then Record rules setup,
        Centralize access rules,
        User wise access rules,
        Show only what is needed for users,
        Access rules setup,
        Easy access rights setup, Hide Any Menu, Any Field, Any Report, Any Button,
        Easy To Configure,
        
        Main Features:-
            Hide fields,
            Hide Buttons,
            Hide Tabs,
            Hide views,
            Hide Contacts,
            Hide Menus,
            Hide submenus,
            Hide sub-menus,
            Hide reports,
            Hide actions,
            Hide server actions,
            Hide import,
            Hide delete,
            Hide archive,
            Hide Tree view, 
            Hide Form view, 
            Hide Kanban view, 
            Hide Calendar view, 
            Hide Pivot,
            Hide Graph view,
            Hide Apps,
            Hide object buttons,
            Hide action buttons,
            Hide smart buttons,
            Readonly Any Field,
            read only user,
            readonly user,
            Hide create,
            Hide duplicate,
            Control every fields,
            Control every views,
            Control every buttons,
            Control every actions
    """,
    "images": ["static/description/icon.png"],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'data/view_data.xml',
        'views/access_management_view.xml',
        'views/res_users_view.xml',
        'views/store_model_nodes_view.xml',
        'views/templates.xml',
    ],
    'depends': ['web', 'advanced_web_domain_widget', 'project_enterprise'],
    'post_init_hook': 'post_install_action_dup_hook',
    'application': True,
    'installable': True,
    'auto_install': False,
}
