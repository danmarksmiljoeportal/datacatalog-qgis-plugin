SOURCES = __init__.py \
          plugin.py \
          constants.py \
          core/data_classes.py \
          core/data_parser_task.py \
          core/data_registry.py \
          core/file_downloader_task.py \
          core/settings_registry.py \
          core/utils.py \
          gui/dataset_item_model.py \
          gui/dataset_tree_view.py \
          gui/details_dialog.py \
          gui/dock_widget.py
          gui/options_widget.py

FORMS = ui/catalogue_widget.ui \
        ui/details_dialog.ui \
        ui/options_widget.ui

TRANSLATIONS = i18n/dmpcatalogue_da.ts \
               i18n/dmpcatalogue_fr.ts \
               i18n/dmpcatalogue_de.ts \
               i18n/dmpcatalogue_vn.ts \
               i18n/dmpcatalogue_uk.ts
