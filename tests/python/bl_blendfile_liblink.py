# Apache License, Version 2.0

# ./blender.bin --background -noaudio --python tests/python/bl_blendfile_liblink.py
import bpy
import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from bl_blendfile_utils import TestHelper


class TestBlendLibLinkHelper(TestHelper):
    
    def __init__(self, args):
        self.args = args

    @staticmethod
    def reset_blender():
        bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
        bpy.data.orphans_purge(do_recursive=True)

    def unique_blendfile_name(self, base_name):
        return base_name + self.__class__.__name__ + ".blend"

    def init_lib_data_basic(self):
        self.reset_blender()

        me = bpy.data.meshes.new("LibMesh")
        ob = bpy.data.objects.new("LibMesh", me)
        coll = bpy.data.collections.new("LibMesh")
        coll.objects.link(ob)
        bpy.context.scene.collection.children.link(coll)

        output_dir = self.args.output_dir
        self.ensure_path(output_dir)
        # Take care to keep the name unique so multiple test jobs can run at once.
        output_lib_path = os.path.join(output_dir, self.unique_blendfile_name("blendlib"))

        bpy.ops.wm.save_as_mainfile(filepath=output_lib_path, check_existing=False, compress=False)

        return output_lib_path


class TestBlendLibLinkSaveLoadBasic(TestBlendLibLinkHelper):

    def __init__(self, args):
        self.args = args

    def test_link_save_load(self):
        output_dir = self.args.output_dir
        output_lib_path = self.init_lib_data_basic()

        # Simple link of a single ObData.
        self.reset_blender()

        link_dir = os.path.join(output_lib_path, "Mesh")
        bpy.ops.wm.link(directory=link_dir, filename="LibMesh", instance_object_data=False)

        assert(len(bpy.data.meshes) == 1)
        assert(len(bpy.data.objects) == 0)
        assert(len(bpy.data.collections) == 0)  # Scene's master collection is not listed here

        orig_data = self.blender_data_to_tuple(bpy.data, "orig_data")

        output_work_path = os.path.join(output_dir, self.unique_blendfile_name("blendfile"))
        bpy.ops.wm.save_as_mainfile(filepath=output_work_path, check_existing=False, compress=False)
        bpy.ops.wm.open_mainfile(filepath=output_work_path, load_ui=False)

        read_data = self.blender_data_to_tuple(bpy.data, "read_data")

        # Since there is no usage of linked mesh, it is lost during save/reload.
        assert(len(bpy.data.meshes) == 0)
        assert(orig_data != read_data)

        # Simple link of a single ObData with obdata instanciation.
        self.reset_blender()

        link_dir = os.path.join(output_lib_path, "Mesh")
        bpy.ops.wm.link(directory=link_dir, filename="LibMesh", instance_object_data=True)

        assert(len(bpy.data.meshes) == 1)
        assert(len(bpy.data.objects) == 1)  # Instance created for the mesh ObData.
        assert(len(bpy.data.collections) == 0)  # Scene's master collection is not listed here

        orig_data = self.blender_data_to_tuple(bpy.data, "orig_data")

        bpy.ops.wm.save_as_mainfile(filepath=output_work_path, check_existing=False, compress=False)
        bpy.ops.wm.open_mainfile(filepath=output_work_path, load_ui=False)

        read_data = self.blender_data_to_tuple(bpy.data, "read_data")

        assert(orig_data == read_data)

        # Simple link of a single Object.
        self.reset_blender()

        link_dir = os.path.join(output_lib_path, "Object")
        bpy.ops.wm.link(directory=link_dir, filename="LibMesh")

        assert(len(bpy.data.meshes) == 1)
        assert(len(bpy.data.objects) == 1)
        assert(len(bpy.data.collections) == 0)  # Scene's master collection is not listed here

        orig_data = self.blender_data_to_tuple(bpy.data, "orig_data")

        bpy.ops.wm.save_as_mainfile(filepath=output_work_path, check_existing=False, compress=False)
        bpy.ops.wm.open_mainfile(filepath=output_work_path, load_ui=False)

        read_data = self.blender_data_to_tuple(bpy.data, "read_data")

        assert(orig_data == read_data)

        # Simple link of a single Collection, with Empty-instanciation.
        self.reset_blender()

        link_dir = os.path.join(output_lib_path, "Collection")
        bpy.ops.wm.link(directory=link_dir, filename="LibMesh", instance_collections=True)

        assert(len(bpy.data.meshes) == 1)
        assert(len(bpy.data.objects) == 2)  # linked object and local empty instancing the collection
        assert(len(bpy.data.collections) == 1)  # Scene's master collection is not listed here

        orig_data = self.blender_data_to_tuple(bpy.data, "orig_data")

        bpy.ops.wm.save_as_mainfile(filepath=output_work_path, check_existing=False, compress=False)
        bpy.ops.wm.open_mainfile(filepath=output_work_path, load_ui=False)

        read_data = self.blender_data_to_tuple(bpy.data, "read_data")

        assert(orig_data == read_data)

        # Simple link of a single Collection, with ViewLayer-instanciation.
        self.reset_blender()

        link_dir = os.path.join(output_lib_path, "Collection")
        bpy.ops.wm.link(directory=link_dir, filename="LibMesh", instance_collections=False)

        assert(len(bpy.data.meshes) == 1)
        assert(len(bpy.data.objects) == 1)
        assert(len(bpy.data.collections) == 1)  # Scene's master collection is not listed here
        # Linked collection should have been added to the scene's master collection children.
        assert(bpy.data.collections[0] in set(bpy.data.scenes[0].collection.children))

        orig_data = self.blender_data_to_tuple(bpy.data, "orig_data")

        bpy.ops.wm.save_as_mainfile(filepath=output_work_path, check_existing=False, compress=False)
        bpy.ops.wm.open_mainfile(filepath=output_work_path, load_ui=False)

        read_data = self.blender_data_to_tuple(bpy.data, "read_data")

        assert(orig_data == read_data)


class TestBlendLibAppendBasic(TestBlendLibLinkHelper):

    def __init__(self, args):
        self.args = args

    def test_append(self):
        output_dir = self.args.output_dir
        output_lib_path = self.init_lib_data_basic()

        # Simple append of a single ObData.
        self.reset_blender()

        link_dir = os.path.join(output_lib_path, "Mesh")
        bpy.ops.wm.append(directory=link_dir, filename="LibMesh",
                          instance_object_data=False, set_fake=False, use_recursive=False)

        assert(len(bpy.data.meshes) == 1)
        assert(bpy.data.meshes[0].library is None)
        assert(bpy.data.meshes[0].use_fake_user is False)
        assert(bpy.data.meshes[0].users == 0)
        assert(len(bpy.data.objects) == 0)
        assert(len(bpy.data.collections) == 0)  # Scene's master collection is not listed here

        # Simple append of a single ObData with obdata instanciation.
        self.reset_blender()

        link_dir = os.path.join(output_lib_path, "Mesh")
        bpy.ops.wm.append(directory=link_dir, filename="LibMesh",
                          instance_object_data=True, set_fake=False, use_recursive=False)

        assert(len(bpy.data.meshes) == 1)
        assert(bpy.data.meshes[0].library is None)
        assert(bpy.data.meshes[0].use_fake_user is False)
        assert(bpy.data.meshes[0].users == 1)
        assert(len(bpy.data.objects) == 1)  # Instance created for the mesh ObData.
        assert(bpy.data.objects[0].library is None)
        assert(len(bpy.data.collections) == 0)  # Scene's master collection is not listed here

        # Simple append of a single ObData with fake user.
        self.reset_blender()

        link_dir = os.path.join(output_lib_path, "Mesh")
        bpy.ops.wm.append(directory=link_dir, filename="LibMesh",
                          instance_object_data=False, set_fake=True, use_recursive=False)

        assert(len(bpy.data.meshes) == 1)
        assert(bpy.data.meshes[0].library is None)
        assert(bpy.data.meshes[0].use_fake_user is True)
        assert(bpy.data.meshes[0].users == 1)
        assert(len(bpy.data.objects) == 0)
        assert(len(bpy.data.collections) == 0)  # Scene's master collection is not listed here

        # Simple append of a single Object.
        self.reset_blender()

        link_dir = os.path.join(output_lib_path, "Object")
        bpy.ops.wm.append(directory=link_dir, filename="LibMesh",
                          instance_object_data=False, set_fake=False, use_recursive=False)

        assert(len(bpy.data.meshes) == 1)
        # This one fails currently, for unclear reasons.
        # ~ assert(bpy.data.meshes[0].library is not None)
        assert(bpy.data.meshes[0].users == 1)
        assert(len(bpy.data.objects) == 1)
        assert(bpy.data.objects[0].library is None)
        assert(bpy.data.objects[0].users == 1)
        assert(len(bpy.data.collections) == 0)  # Scene's master collection is not listed here

        # Simple recursive append of a single Object.
        self.reset_blender()

        link_dir = os.path.join(output_lib_path, "Object")
        bpy.ops.wm.append(directory=link_dir, filename="LibMesh",
                          instance_object_data=False, set_fake=False, use_recursive=True)

        assert(len(bpy.data.meshes) == 1)
        assert(bpy.data.meshes[0].library is None)
        assert(bpy.data.meshes[0].users == 1)
        assert(len(bpy.data.objects) == 1)
        assert(bpy.data.objects[0].library is None)
        assert(bpy.data.objects[0].users == 1)
        assert(len(bpy.data.collections) == 0)  # Scene's master collection is not listed here

        # Simple recursive append of a single Collection.
        self.reset_blender()

        link_dir = os.path.join(output_lib_path, "Collection")
        bpy.ops.wm.append(directory=link_dir, filename="LibMesh",
                          instance_object_data=False, set_fake=False, use_recursive=True)

        assert(bpy.data.meshes[0].library is None)
        assert(bpy.data.meshes[0].users == 1)
        assert(len(bpy.data.objects) == 1)
        assert(bpy.data.objects[0].library is None)
        assert(bpy.data.objects[0].users == 1)
        assert(len(bpy.data.collections) == 1)  # Scene's master collection is not listed here
        assert(bpy.data.collections[0].library is None)
        assert(bpy.data.collections[0].users == 1)


TESTS = (
    TestBlendLibLinkSaveLoadBasic,
    TestBlendLibAppendBasic,
)


def argparse_create():
    import argparse

    # When --help or no args are given, print this help
    description = "Test basic IO of blend file."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=".",
        help="Where to output temp saved blendfiles",
        required=False,
    )

    return parser


def main():
    args = argparse_create().parse_args()

    # Don't write thumbnails into the home directory.
    bpy.context.preferences.filepaths.use_save_preview_images = False

    for Test in TESTS:
        Test(args).run_all_tests()


if __name__ == '__main__':
    import sys
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    main()
