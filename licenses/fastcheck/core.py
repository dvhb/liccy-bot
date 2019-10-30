from licenses.main.models import LicensesList


def db_fastcheck(license):
    q = LicensesList.query.filter(LicensesList.license_name.like(license)).first()
    if q is not None and q.license_type:
        return True
    elif q is not None and q.license_type is None:
        return None
    else:
        return False
