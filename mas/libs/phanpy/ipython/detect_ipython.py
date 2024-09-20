def is_ipynb() -> bool:
    try:
        ipy = get_ipython()  # type: ignore
        if ipy is None:
            return False

        shell = ipy.__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True
        elif shell == "TerminalInteractiveShell":
            return False

        return False
    except ImportError:
        return False
    except NameError:
        return False
    except Exception:
        return False
