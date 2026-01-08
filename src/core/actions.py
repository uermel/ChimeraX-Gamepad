# vim: set expandtab shiftwidth=4 softtabstop=4:


class ViewAction:
    """Applies gamepad input to camera/view manipulation."""

    def __init__(self, session, config):
        """Initialize the view action handler.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        config : GamepadConfig
            The gamepad configuration.
        """
        self.session = session
        self.config = config

    @property
    def view(self):
        """Get the main view.

        Returns
        -------
        chimerax.graphics.View
            The main view.
        """
        return self.session.main_view

    def apply(self, pan_x, pan_y, rotate_x, rotate_y, zoom):
        """Apply view transformations based on gamepad input.

        Parameters
        ----------
        pan_x : float
            Left stick X axis (-1 to 1) for horizontal panning.
        pan_y : float
            Left stick Y axis (-1 to 1) for vertical panning.
        rotate_x : float
            Right stick X axis (-1 to 1) for horizontal rotation.
        rotate_y : float
            Right stick Y axis (-1 to 1) for vertical rotation.
        zoom : float
            Trigger difference (-1 to 1) for zooming.
        """
        # Skip if all inputs are near zero
        if all(abs(v) < 0.001 for v in [pan_x, pan_y, rotate_x, rotate_y, zoom]):
            return

        sensitivity = self.config.view_sensitivity

        # Rotation (right stick)
        if abs(rotate_x) > 0.001 or abs(rotate_y) > 0.001:
            self._apply_rotation(rotate_x, rotate_y, sensitivity)

        # Pan (left stick)
        if abs(pan_x) > 0.001 or abs(pan_y) > 0.001:
            self._apply_pan(pan_x, pan_y, sensitivity)

        # Zoom (triggers)
        if abs(zoom) > 0.001:
            self._apply_zoom(zoom, sensitivity)

    def _apply_rotation(self, rotate_x, rotate_y, sensitivity):
        """Apply rotation to the view.

        Parameters
        ----------
        rotate_x : float
            Horizontal rotation amount.
        rotate_y : float
            Vertical rotation amount.
        sensitivity : float
            Sensitivity multiplier.
        """
        # Get camera position for coordinate conversion
        camera_pos = self.view.camera.position

        # Rotation speed in degrees per frame
        angle_speed = sensitivity * 2.0

        # Horizontal rotation (around Y axis in camera space -> scene space)
        if abs(rotate_x) > 0.001:
            # Camera Y axis points up, rotating around it spins the view horizontally
            axis = camera_pos.transform_vector((0, 1, 0))
            angle = rotate_x * angle_speed
            self.view.rotate(axis, angle)

        # Vertical rotation (around X axis in camera space -> scene space)
        if abs(rotate_y) > 0.001:
            # Camera X axis points right, rotating around it tilts the view
            axis = camera_pos.transform_vector((1, 0, 0))
            angle = rotate_y * angle_speed
            self.view.rotate(axis, angle)

    def _apply_pan(self, pan_x, pan_y, sensitivity):
        """Apply panning to the view.

        Parameters
        ----------
        pan_x : float
            Horizontal pan amount.
        pan_y : float
            Vertical pan amount.
        sensitivity : float
            Sensitivity multiplier.
        """
        # Get pixel size for scaling
        psize = self.view.pixel_size()
        if psize is None:
            psize = 1.0

        # Pan speed in scene units per frame
        pan_speed = sensitivity * 20.0 * psize

        # Calculate shift in camera coordinates
        shift_cam = (pan_x * pan_speed, -pan_y * pan_speed, 0)

        # Convert to scene coordinates
        camera_pos = self.view.camera.position
        shift_scene = camera_pos.transform_vector(shift_cam)

        self.view.translate(shift_scene)

    def _apply_zoom(self, zoom, sensitivity):
        """Apply zoom to the view.

        Parameters
        ----------
        zoom : float
            Zoom amount (-1 to 1, positive zooms in).
        sensitivity : float
            Sensitivity multiplier.
        """
        v = self.view
        c = v.camera

        # Zoom speed (increased for better responsiveness)
        zoom_speed = sensitivity * 15.0

        # Get pixel size for scaling
        psize = v.pixel_size()
        if psize is None:
            psize = 1.0

        delta_z = zoom * zoom_speed * psize

        if c.name == "orthographic":
            # For orthographic camera, adjust field width
            c.field_width = max(c.field_width - delta_z, psize)
            c.redraw_needed = True
        else:
            # For perspective camera, translate along camera Z axis
            shift = c.position.transform_vector((0, 0, delta_z))
            v.translate(shift)


class ModelAction:
    """Applies gamepad input to selected model manipulation."""

    def __init__(self, session, config):
        """Initialize the model action handler.

        Parameters
        ----------
        session : chimerax.core.session.Session
            The ChimeraX session.
        config : GamepadConfig
            The gamepad configuration.
        """
        self.session = session
        self.config = config

    @property
    def view(self):
        """Get the main view.

        Returns
        -------
        chimerax.graphics.View
            The main view.
        """
        return self.session.main_view

    def apply(self, translate_x, translate_y, rotate_x, rotate_y, translate_z):
        """Apply model transformations based on gamepad input.

        Parameters
        ----------
        translate_x : float
            Left stick X axis (-1 to 1) for X translation.
        translate_y : float
            Left stick Y axis (-1 to 1) for Y translation.
        rotate_x : float
            Right stick X axis (-1 to 1) for horizontal rotation.
        rotate_y : float
            Right stick Y axis (-1 to 1) for vertical rotation.
        translate_z : float
            Trigger difference (-1 to 1) for Z translation.
        """
        # Get selected models
        models = self._get_selected_models()
        if not models:
            return

        # Skip if all inputs are near zero
        if all(abs(v) < 0.001 for v in [translate_x, translate_y, rotate_x, rotate_y, translate_z]):
            return

        sensitivity = self.config.model_sensitivity

        # Rotation (right stick)
        if abs(rotate_x) > 0.001 or abs(rotate_y) > 0.001:
            self._apply_rotation(models, rotate_x, rotate_y, sensitivity)

        # Translation XY (left stick)
        if abs(translate_x) > 0.001 or abs(translate_y) > 0.001:
            self._apply_translation_xy(models, translate_x, translate_y, sensitivity)

        # Translation Z (triggers)
        if abs(translate_z) > 0.001:
            self._apply_translation_z(models, translate_z, sensitivity)

    def _get_selected_models(self):
        """Get the list of selected models that can be transformed.

        Returns
        -------
        list
            List of selected models with position attribute.
        """
        # Get top-level selected models
        from chimerax.core.models import Model

        selected = []
        for m in self.session.selection.models():
            # Only include top-level models with position attribute
            if (
                isinstance(m, Model)
                and hasattr(m, "position")
                and (m.parent is None or m.parent is self.session.models.scene_root_model)
            ):
                selected.append(m)

        return selected

    def _apply_rotation(self, models, rotate_x, rotate_y, sensitivity):
        """Apply rotation to models.

        Parameters
        ----------
        models : list
            List of models to rotate.
        rotate_x : float
            Horizontal rotation amount.
        rotate_y : float
            Vertical rotation amount.
        sensitivity : float
            Sensitivity multiplier.
        """
        from chimerax.geometry import rotation

        # Get camera position for coordinate conversion
        camera_pos = self.view.camera.position

        # Rotation speed in degrees per frame
        angle_speed = sensitivity * 2.0

        for model in models:
            # Get rotation center (model center)
            center = self._get_model_center(model)

            current_pos = model.position

            # Horizontal rotation (around camera Y axis)
            if abs(rotate_x) > 0.001:
                axis = camera_pos.transform_vector((0, 1, 0))
                angle = rotate_x * angle_speed
                rot = rotation(axis, angle, center)
                current_pos = rot * current_pos

            # Vertical rotation (around camera X axis)
            if abs(rotate_y) > 0.001:
                axis = camera_pos.transform_vector((1, 0, 0))
                angle = rotate_y * angle_speed
                rot = rotation(axis, angle, center)
                current_pos = rot * current_pos

            model.position = current_pos

    def _apply_translation_xy(self, models, translate_x, translate_y, sensitivity):
        """Apply XY translation to models.

        Parameters
        ----------
        models : list
            List of models to translate.
        translate_x : float
            X translation amount.
        translate_y : float
            Y translation amount.
        sensitivity : float
            Sensitivity multiplier.
        """
        from chimerax.geometry import translation

        # Get pixel size for scaling
        psize = self.view.pixel_size()
        if psize is None:
            psize = 1.0

        # Translation speed in scene units per frame
        trans_speed = sensitivity * 20.0 * psize

        # Calculate shift in camera coordinates
        shift_cam = (translate_x * trans_speed, -translate_y * trans_speed, 0)

        # Convert to scene coordinates
        camera_pos = self.view.camera.position
        shift_scene = camera_pos.transform_vector(shift_cam)

        trans = translation(shift_scene)

        for model in models:
            model.position = trans * model.position

    def _apply_translation_z(self, models, translate_z, sensitivity):
        """Apply Z translation to models.

        Parameters
        ----------
        models : list
            List of models to translate.
        translate_z : float
            Z translation amount.
        sensitivity : float
            Sensitivity multiplier.
        """
        from chimerax.geometry import translation

        # Get pixel size for scaling
        psize = self.view.pixel_size()
        if psize is None:
            psize = 1.0

        # Translation speed in scene units per frame (increased for better responsiveness)
        trans_speed = sensitivity * 60.0 * psize

        # Calculate shift in camera coordinates (along camera Z)
        shift_cam = (0, 0, translate_z * trans_speed)

        # Convert to scene coordinates
        camera_pos = self.view.camera.position
        shift_scene = camera_pos.transform_vector(shift_cam)

        trans = translation(shift_scene)

        for model in models:
            model.position = trans * model.position

    def _get_model_center(self, model):
        """Get the center point of a model for rotation.

        Parameters
        ----------
        model : Model
            The model to get the center of.

        Returns
        -------
        tuple
            (x, y, z) center point in scene coordinates.
        """
        if hasattr(model, "bounds"):
            bounds = model.bounds()
            if bounds is not None:
                return tuple(bounds.center())
        return (0, 0, 0)
