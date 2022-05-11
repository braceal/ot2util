import inspect
from pathlib import Path
from typing import Union, List, Callable, Any, Dict
from opentrons.protocol_api import ProtocolContext
from jinja2 import Environment, PackageLoader
from ot2util.config import ProtocolConfig, MetaDataConfig, PathLike


def _getsource(func: Callable[..., Any]) -> str:
    code = inspect.getsource(func)
    lines = code.split("\n")
    indent = len(lines[0]) - len(lines[0].lstrip())
    lines = [line[indent:] for line in lines]
    code = "\n".join(lines)
    return code


def get_function_source_codes(funcs: List[Callable[..., Any]]) -> List[str]:
    # TODO: Should copy into template in the order they are passed
    source_codes = [_getsource(func) for func in funcs]
    return source_codes


def to_template(
    imports: Callable[[], None],
    config_class: ProtocolConfig,
    run_func: Callable[[ProtocolContext], None],
    metadata: MetaDataConfig,
    funcs: List[Callable[..., Any]] = [],
    template_file: str = "protocol.j2",
) -> str:
    function_codes = get_function_source_codes(funcs + [run_func])
    context = {
        "imports": _getsource(imports),
        "config_code": inspect.getsource(config_class),  # type: ignore[arg-type]
        "metadata": metadata,
        "function_codes": function_codes,
    }
    env = Environment(
        loader=PackageLoader("ot2util"),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    template = env.get_template(template_file)
    return template.render(context)


def write_template(filename: PathLike, *args: Any, **kwargs: Any) -> Path:
    with open(filename, "w") as fp:
        txt = to_template(*args, **kwargs)
        fp.write(txt)
    return Path(fp.name)


class Gym:
    config_class: ProtocolConfig = ProtocolConfig()

    def __init__(self, metadata: Union[MetaDataConfig, Dict[str, str]]) -> None:
        if isinstance(metadata, MetaDataConfig):
            self.metadata = metadata
        else:
            self.metadata = MetaDataConfig(**metadata)

    def generate_template(
        self,
        protocol_path: PathLike,
        funcs: List[Callable[..., Any]] = [],
        template_file: str = "protocol.j2",
    ) -> None:
        write_template(
            protocol_path,
            imports=self.imports,
            config_class=self.config_class,
            run_func=self.run,
            metadata=self.metadata,
            funcs=funcs,
            template_file=template_file,
        )

    def imports(self) -> None:
        """Include imports here."""
        pass

    def run(self) -> None:
        """Implement opentrons protocol here."""
        pass
