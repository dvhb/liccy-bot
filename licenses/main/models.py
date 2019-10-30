from licenses import db


class Licenses(db.Model):
    __tablename__ = 'licenses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    license = db.Column(db.String)
    package_type = db.Column(db.String)
    project = db.Column(db.String)

    def __init__(self, name, license, package_type, project):
        self.name = name
        self.license = license
        self.package_type = package_type
        self.project = project


class LicensesList(db.Model):
    __tablename__ = 'licenses_list'
    id = db.Column(db.Integer, primary_key=True)
    license_name = db.Column(db.String)
    license_type = db.Column(db.Boolean)

    def __repr__(self):
        return '<License %r>' % self.license_name
