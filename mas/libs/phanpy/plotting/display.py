import json

from mas.libs.phanpy.plotting.layer.renderable import RenderableTrait
from mas.libs.phanpy.plotting.options import plotting_options
from mas.libs.phanpy.plotting.setup import setup, setup_notebook


class PlotDisplay(RenderableTrait):
    def _ipython_display_(self) -> None:
        """Display in ipython"""

        if plotting_options.static_in_nb:
            from bokeh.embed import json_item
            from IPython.display import publish_display_data

            publish_display_data(
                {
                    "application/vnd.bokehjs.mas.v1+json": json.dumps(
                        json_item(self.render())
                    ),
                }
            )
        else:
            self.show()

    def _repr_html_(self) -> str:
        from bokeh.plotting import show

        setup_notebook()

        display = show(self.render())
        if not display:
            return ""

        return display._repr_html_()

    def show(self) -> None:
        from bokeh.plotting import show

        setup()

        show(self.render())
