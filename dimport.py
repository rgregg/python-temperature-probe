from importlib import import_module

def dynload(module_name, class_name, *args):
    module = import_module(module_name)
    assert hasattr(module, class_name), "class {} is not in {}".format(class_name, module_name)
    my_class = getattr(module, class_name)
    return my_class(*args)