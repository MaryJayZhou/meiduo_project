# 封装面包屑组件

def get_breadcrumb(cat3):
    # 1.三级 --->二级
    cat2 = cat3.parent

    # 2. 二级 --->一级
    cat1 = cat2.parent

    breadcumb = {
        'cat1': {
            'id': cat1.id,
            'name': cat1.name,
            'url': cat1.goodschannel_set.all()[0].url
        },
        'cat2': cat2,
        'cat3': cat3,
    }
    return breadcumb
