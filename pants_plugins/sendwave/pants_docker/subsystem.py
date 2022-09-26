"""Configuration for the Sendwave pants-docker plugin."""
from pants.engine.rules import SubsystemRule
from pants.option.option_types import BoolOption
from pants.option.subsystem import Subsystem


class Docker(Subsystem):
    """Options for Docker Plugin.

    Allow configuring plugin behavior under the [docker] scope in your
    pants.toml, or by passing --docker-{option-name} to your command.
    Available Options:

    report-progress (boolean): if true, log the output of the docker
        build process.
    """

    options_scope = "sendwave-docker"
    help = "Options for Docker Build Process."

    report_progress = BoolOption(
        "--report-progress",
        default=False,
        help="If true: the plugin will report output of `docker build`",
    )


def rules():
    """Register Docker options as a SubsystemRule."""
    return [SubsystemRule(Docker)]
