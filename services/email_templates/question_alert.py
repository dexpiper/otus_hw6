email_template = (
    'Hello, {username}!\n'
    'You have a new answer on your question "{qw_title}" on Hasker. '
    'Would you like to check it out? \n'
    '{qw_link}'
    '\n\nIf you do not want email alerts anymore, turn them off in your'
    ' profile: {profile_link}'
)

html_email_temlate = (
    '<p>Hello, {username}!</p>'
    '<p>You have a new answer on your question "{qw_title}" on Hasker. '
    'Would you like to check it out?</p>'
    '<p><a href="{qw_link}">Here is your link!</a></p>'
    '<p>If you do not want email alerts anymore, turn them off in your'
    ' <a href="{profile_link}">profile</a>.</p>'
)
