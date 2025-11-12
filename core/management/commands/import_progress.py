from decimal import Decimal
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from core.models import Project, CostCode, BudgetLine, BudgetProgress
import io
import csv
from urllib.parse import urlparse
from urllib.request import urlopen

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y")

def parse_date(s: str):
    s = (s or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Fecha inválida: {s}")

def to_decimal(val, default=None):
    if val in (None, "", " "):
        return default
    return Decimal(str(val).strip())

def open_csv_source(path_or_url: str):
    parsed = urlparse(path_or_url)
    if parsed.scheme in ('http', 'https'):
        # Lee CSV remoto (UTF-8) desde una URL
        resp = urlopen(path_or_url)
        return io.TextIOWrapper(resp, encoding='utf-8')
    # Archivo local
    return open(path_or_url, newline='', encoding='utf-8')

def dict_reader_from_io(f):
    text = f.read()
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')
    # Quita BOM
    text = text.lstrip('\ufeff')
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[',',';','\t'])
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ','
    return csv.DictReader(io.StringIO(text), delimiter=delimiter)

class Command(BaseCommand):
    help = "Importa BudgetProgress desde CSV. Encabezados: project_id,cost_code,date,percent_complete,qty_completed,note"

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Ruta al CSV')
        parser.add_argument('--project', type=int, help='ID de proyecto por defecto si no viene en CSV')
        parser.add_argument('--dry-run', action='store_true', help='No guarda, solo muestra')

    def handle(self, *args, **opts):
        path = opts['csv_path']
        default_project_id = opts.get('project')
        dry = opts['dry_run']

        try:
            with open_csv_source(path) as f:
                reader = dict_reader_from_io(f)
                headers = {h.lower(): h for h in (reader.fieldnames or [])}
                required = {'cost_code', 'date'}
                if not required.issubset(set(headers.keys())):
                    raise CommandError(f"Encabezados requeridos: {sorted(required)}")

                created = updated = skipped = 0

                for i, row in enumerate(reader, start=2):
                    try:
                        project_id = row.get(headers.get('project_id')) or default_project_id
                        if not project_id:
                            raise ValueError("Falta project_id (o usa --project).")
                        project = Project.objects.get(pk=int(project_id))

                        cc_code = (row.get(headers['cost_code']) or "").strip()
                        if not cc_code:
                            raise ValueError("Falta cost_code.")
                        try:
                            cost_code = CostCode.objects.get(code=cc_code)
                        except CostCode.DoesNotExist:
                            raise ValueError(f"CostCode no existe: {cc_code}")

                        bl = BudgetLine.objects.filter(project=project, cost_code=cost_code).order_by('id').first()
                        if not bl:
                            raise ValueError(f"No hay BudgetLine para project={project.id} y cost_code={cc_code}")

                        date = parse_date(row.get(headers['date']))
                        percent = to_decimal(row.get(headers.get('percent_complete')), default=None)
                        qty = to_decimal(row.get(headers.get('qty_completed')), default=Decimal('0'))
                        note = (row.get(headers.get('note')) or "").strip()

                        # Autocalcular % si falta y hay qty total
                        if (percent is None or percent == 0) and getattr(bl, 'qty', None):
                            if bl.qty and bl.qty != 0 and qty:
                                percent = min(Decimal('100'), (qty / Decimal(bl.qty)) * Decimal('100'))

                        if percent is not None and (percent < 0 or percent > 100):
                            raise ValueError("percent_complete fuera de 0–100.")

                        obj, is_created = BudgetProgress.objects.get_or_create(
                            budget_line=bl, date=date,
                            defaults={'qty_completed': qty or 0, 'percent_complete': percent or 0, 'note': note}
                        )
                        if is_created:
                            if not dry:
                                obj.full_clean()
                                obj.save()
                            created += 1
                        else:
                            obj.qty_completed = qty if qty is not None else obj.qty_completed
                            if percent is not None:
                                obj.percent_complete = percent
                            if note:
                                obj.note = note
                            if not dry:
                                obj.full_clean()
                                obj.save()
                            updated += 1

                    except Exception as e:
                        skipped += 1
                        self.stderr.write(f"Fila {i}: {e}")

                self.stdout.write(self.style.SUCCESS(
                    f"Listo. created={created}, updated={updated}, skipped={skipped}, dry_run={dry}"
                ))
        except FileNotFoundError:
            raise CommandError(f"No se encuentra el archivo: {path}")