import operator


from django.pwt import Branch
from django.utils.functional import cached_property


class QsMixin:

    @cached_property
    def compiler(self):
        return self.query.get_compiler(using=self.db)

    branch = Branch.Descriptor()

    @branch
    async def _fetch_all(self):
        if self._result_cache is None:
            rows = await self.compiler.execute_sql()
            self._result_cache = self._make_objects(rows)
        if self._prefetch_related_lookups and not self._prefetch_done:
            await self._prefetch_related_objects()
        return self._result_cache

    @branch
    def _fetch_all(self):
        if self._result_cache is None:
            rows = self.compiler.execute_sql()
            self._result_cache = self._make_objects(rows)
        if self._prefetch_related_lookups and not self._prefetch_done:
            self._prefetch_related_objects()
        return self._result_cache

    def __await__(self):
        #TODO rename _fetch_all
        return self._fetch_all().__await__()

    #TODO do not store the connection!
    # get a testcase
    # def iterate(self):
    #     compiler = self.compiler
    #     sql, params = compiler.as_sql()
    #     with compiler.connection.cursor() as cursor:
    #         cursor.execute(sql, params)
    #         rows = cursor.fetchmany(size=1)
    #         yield from self._make_objects(rows)

    def _make_objects(self, rows):
        from django.db.models.query import get_related_populators
        compiler = self.compiler
        # Execute the query. This will also fill compiler.select, klass_info,
        # and annotations.
        rows = compiler.apply_converters_(rows)
        select, klass_info, annotation_col_map = (compiler.select, compiler.klass_info,
                                                  compiler.annotation_col_map)
        model_cls = klass_info['model']
        select_fields = klass_info['select_fields']
        model_fields_start, model_fields_end = select_fields[0], select_fields[-1] + 1
        init_list = [f[0].target.attname
                     for f in select[model_fields_start:model_fields_end]]
        related_populators = get_related_populators(klass_info, select, self.db)
        known_related_objects = [
            (field, related_objs, operator.attrgetter(*[
                field.attname
                if from_field == 'self' else
                self.model._meta.get_field(from_field).attname
                for from_field in field.from_fields
            ])) for field, related_objs in self._known_related_objects.items()
        ]
        objects = []
        for row in rows:
            obj = model_cls.from_db(self.db, init_list, row[model_fields_start:model_fields_end])
            for rel_populator in related_populators:
                rel_populator.populate(row, obj)
            if annotation_col_map:
                for attr_name, col_pos in annotation_col_map.items():
                    setattr(obj, attr_name, row[col_pos])

            # Add the known related objects to the model.
            for field, rel_objs, rel_getter in known_related_objects:
                # Avoid overwriting objects loaded by, e.g., select_related().
                if field.is_cached(obj):
                    continue
                rel_obj_id = rel_getter(obj)
                try:
                    rel_obj = rel_objs[rel_obj_id]
                except KeyError:
                    pass  # May happen in qs1 | qs2 scenarios.
                else:
                    setattr(obj, field.name, rel_obj)

            objects.append(obj)

        return objects
