from django.shortcuts import render


def render_with_error(func, request, errormsg='Some error has occured'):
    r = func(request, fallback=True)
    assert len(r) == 3
    r[2].update({'error_message': errormsg})
    return render(request=r[0], template_name=r[1], context=r[2])
