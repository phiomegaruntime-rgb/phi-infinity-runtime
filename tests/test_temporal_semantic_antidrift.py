
import ast
from pathlib import Path


FORBIDDEN = {
    "d_tau",
    "mean_dtau",
}


def parent_map(tree):

    result = {}

    for parent in ast.walk(tree):

        for child in ast.iter_child_nodes(
            parent
        ):
            result[child] = parent

    return result


def is_explicit_removal_guard(
    node,
    parents,
):

    parent = parents.get(node)

    if not isinstance(
        parent,
        ast.Call,
    ):
        return False

    if not isinstance(
        parent.func,
        ast.Attribute,
    ):
        return False

    if parent.func.attr != "pop":
        return False

    if not parent.args:
        return False

    return parent.args[0] is node


def test_obsolete_temporal_aliases_cannot_reenter_runtime_semantics():

    violations = []

    for path in Path(
        "src"
    ).rglob(
        "*.py"
    ):

        source = path.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(
            source,
            filename=str(path),
        )

        parents = parent_map(
            tree
        )

        for node in ast.walk(
            tree
        ):

            if (
                isinstance(
                    node,
                    ast.Name,
                )
                and
                node.id in FORBIDDEN
            ):

                violations.append(
                    (
                        str(path),
                        node.lineno,
                        "identifier",
                        node.id,
                    )
                )

            elif (
                isinstance(
                    node,
                    ast.arg,
                )
                and
                node.arg in FORBIDDEN
            ):

                violations.append(
                    (
                        str(path),
                        node.lineno,
                        "argument",
                        node.arg,
                    )
                )

            elif (
                isinstance(
                    node,
                    ast.Attribute,
                )
                and
                node.attr in FORBIDDEN
            ):

                violations.append(
                    (
                        str(path),
                        node.lineno,
                        "attribute",
                        node.attr,
                    )
                )

            elif (
                isinstance(
                    node,
                    ast.Constant,
                )
                and
                isinstance(
                    node.value,
                    str,
                )
                and
                node.value in FORBIDDEN
            ):

                if not is_explicit_removal_guard(
                    node,
                    parents,
                ):

                    violations.append(
                        (
                            str(path),
                            node.lineno,
                            "string",
                            node.value,
                        )
                    )

    assert not violations, violations


def test_current_temporal_closure_remains_explicit():

    closure = Path(
        "docs/TEMPORAL_BRANCH_CLOSURE_CURRENT.md"
    ).read_text(
        encoding="utf-8"
    )

    required = [
        r"\lambda_{\mathcal M} \neq \tau",
        r"\mathcal C_{ij}",
        r"\Sigma_{ij}",
        r"q_{ij}",
        r"\frac{\rho_i}{\rho_j}",
        "TEMPORAL ARCHITECTURE: PROVISIONALLY CLOSED",
        "UNIVERSAL QUANTITATIVE LAW: OPEN",
    ]

    for fragment in required:
        assert fragment in closure
