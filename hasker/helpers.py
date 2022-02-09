from django.shortcuts import render


def render_with_error(func, request,
                      errormsg='Some error has occured',
                      **kwargs):
    r = func(request, fallback=True)
    if not len(r) == 3:
        if not isinstance(r[-1], dict):
            r[2] = {}
    r[2].update({'error_message': errormsg})
    if kwargs:
        r[2].update(kwargs)
    return render(request=r[0], template_name=r[1], context=r[2])
