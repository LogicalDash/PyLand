class Attribute:
    def __init__(name, permitted_vals):
        self.name = name
        if type(permitted_vals) is list:
            def test_membership(self, it):
                return it in permitted_vals
        elif type(permitted_vals) is function:
            def test_membership(self, it):
                return permitted_vals(it)
        else:
            def test_membership(self, it):
                return True
        self.test_membership = test_membership
