"""Regression checks for metadata that must load before the IDE can offer Debug/Release."""

import unittest
from pathlib import Path
from xml.dom import Node, minidom

PROJECT = Path(__file__).resolve().parents[1] / "firmware" / "PRUMO"


class ProjectMetadataTests(unittest.TestCase):
    def test_cdt_storage_header_and_configurations(self):
        doc = minidom.parse(str(PROJECT / ".cproject"))
        # CDT's storage loader reads the first DOM node, not just the XML root.
        first = doc.firstChild
        self.assertEqual(first.nodeType, Node.PROCESSING_INSTRUCTION_NODE)
        self.assertEqual(first.target, "fileVersion")
        self.assertEqual(first.data, "4.0.0")
        self.assertEqual(doc.documentElement.tagName, "cproject")
        self.assertEqual(
            doc.documentElement.getAttribute("storage_type_id"),
            "org.eclipse.cdt.core.XmlProjectDescriptionStorage",
        )
        configs = doc.getElementsByTagName("cconfiguration")
        names = set()
        for config in configs:
            settings = next(
                child
                for child in config.childNodes
                if child.nodeType == Node.ELEMENT_NODE
                and child.getAttribute("moduleId") == "org.eclipse.cdt.core.settings"
            )
            names.add(settings.getAttribute("name"))
            self.assertEqual(
                settings.getAttribute("buildSystemId"),
                "org.eclipse.cdt.managedbuilder.core.configurationDataProvider",
            )
            self.assertEqual(config.getAttribute("id"), settings.getAttribute("id"))
        self.assertEqual(names, {"Debug", "Release"})

    def test_project_has_builder_and_explicit_utf8(self):
        doc = minidom.parse(str(PROJECT / ".project"))
        names = {node.firstChild.data for node in doc.getElementsByTagName("nature")}
        self.assertIn("org.eclipse.cdt.core.cnature", names)
        self.assertIn("org.eclipse.cdt.managedbuilder.core.managedBuildNature", names)
        builders = {
            node.getElementsByTagName("name")[0].firstChild.data
            for node in doc.getElementsByTagName("buildCommand")
        }
        self.assertIn("org.eclipse.cdt.managedbuilder.core.genmakebuilder", builders)
        prefs = (PROJECT / ".settings" / "org.eclipse.core.resources.prefs").read_text(
            encoding="utf-8"
        )
        self.assertIn("encoding/<project>=UTF-8", prefs.splitlines())


if __name__ == "__main__":
    unittest.main()
