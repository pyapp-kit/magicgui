from magicgui import magicgui


@magicgui(auto_call=True, slider_int={"label" : "val = 10000", "widget_type": "Slider", "value": 10000, "min": 10000, "max": 100000, "step": 10000,},)
def step_demo(slider_int=10000,):
    step_demo.slider_int.label = "val = " + str(slider_int)
    return slider_int



@magicgui(auto_call=True, slider_int={"label" : "val = 500", "widget_type": "Slider", "value": 500, "min": 400, "max": 1000, "step": 100,},)
def step_workaround(slider_int=500,):
    step = step_workaround.slider_int.step
    rem = slider_int % step
    if rem > step_workaround.slider_int.step/2 :
        slider_int += step - rem
    else:
        slider_int -= rem
    step_workaround.slider_int.value = slider_int
    step_workaround.slider_int.label = "val = " + str(slider_int)
    return slider_int


step_demo.show(run=True)
#step_workaround.show(run=True)
